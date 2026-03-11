package main

import (
	"context"
	"database/sql"
	"embed"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/joho/godotenv"
	"github.com/klaital/cardsorter/backend/internal/config"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/metadata"
	"log/slog"
	"net"
	"net/http"
	"os"
	"path"
	"strings"

	_ "github.com/go-sql-driver/mysql"
	pb "github.com/klaital/cardsorter/backend/gen/protos"
	"github.com/klaital/cardsorter/backend/internal/server"
)

//go:embed dist/swagger-ui/*
var swaggerUI embed.FS

//go:embed gen/openapiv2/openapi.swagger.json
var swaggerDoc []byte

// corsMiddleware adds CORS headers to allow requests from frontend
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")

		// Allow localhost on any port and production domains
		allowedOrigins := []string{
			"http://localhost:5173",
			"http://localhost:3000",
			"https://klaital.com",
			"https://abandonedfactory.net",
			"http://abandonedfactory.net",
		}

		// Check if origin is localhost with any port
		if strings.HasPrefix(origin, "http://localhost:") ||
			strings.HasPrefix(origin, "http://127.0.0.1:") {
			w.Header().Set("Access-Control-Allow-Origin", origin)
		} else {
			// Check against allowed origins
			for _, allowed := range allowedOrigins {
				if origin == allowed {
					w.Header().Set("Access-Control-Allow-Origin", origin)
					break
				}
			}
		}

		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Accept, Authorization, Content-Type, X-CSRF-Token")
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		w.Header().Set("Access-Control-Max-Age", "86400")

		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func main() {
	// Load .env file if it exists
	if err := godotenv.Load(); err != nil {
		slog.Debug("No .env file found or error loading it", "err", err)
		// Continue execution as the .env file is optional
	}

	cfg := config.ParseEnv()
	db, err := sql.Open("mysql", cfg.MysqlDbString())
	if err != nil {
		slog.Error("Failed to connect to database", "err", err, "connstring", cfg.MysqlDbStringRedacted())
		os.Exit(1)
	}
	defer db.Close()
	if err := db.Ping(); err != nil {
		slog.Error("failed the initial db ping", "err", err, "connstring", cfg.MysqlDbString())
		// TODO: should we wait/retry here? Do we ever wait for the db to be created?
		os.Exit(1)
	}

	grpcServer := grpc.NewServer(
		grpc.UnaryInterceptor(server.SelectiveAuthInterceptor),
	)

	// Register all services
	pb.RegisterLibraryServiceServer(grpcServer, server.NewLibraryServer(db))
	pb.RegisterUserServiceServer(grpcServer, server.NewUserServer(db))
	pb.RegisterCardServiceServer(grpcServer, server.NewCardServer(db))

	// Start gRPC server
	slog.Debug("Starting gRPC server", "port", cfg.GrpcPort)
	lis, err := net.Listen("tcp", cfg.GrpcPort)
	if err != nil {
		slog.Error("Failed to start gRPC listener", "err", err, "port", cfg.GrpcPort)
		os.Exit(1)
	}
	go grpcServer.Serve(lis)

	// Create gRPC-Gateway mux with metadata annotator to forward auth headers
	gwmux := runtime.NewServeMux(
		runtime.WithMetadata(func(ctx context.Context, req *http.Request) metadata.MD {
			// Forward the Authorization header from HTTP to gRPC metadata
			md := metadata.MD{}
			if auth := req.Header.Get("Authorization"); auth != "" {
				md.Set("authorization", auth)
			}
			return md
		}),
	)
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	grpcEndpoint := "localhost" + cfg.GrpcPort

	// Register all service handlers with the gateway
	err = pb.RegisterLibraryServiceHandlerFromEndpoint(context.Background(), gwmux, grpcEndpoint, opts)
	if err != nil {
		slog.Error("Failed to register LibraryService gateway", "err", err.Error())
		os.Exit(1)
	}

	err = pb.RegisterUserServiceHandlerFromEndpoint(context.Background(), gwmux, grpcEndpoint, opts)
	if err != nil {
		slog.Error("Failed to register UserService gateway", "err", err.Error())
		os.Exit(1)
	}

	err = pb.RegisterCardServiceHandlerFromEndpoint(context.Background(), gwmux, grpcEndpoint, opts)
	if err != nil {
		slog.Error("Failed to register CardService gateway", "err", err.Error())
		os.Exit(1)
	}

	// Create a new mux for handling both API and Swagger UI
	mux := http.NewServeMux()

	// Handle API requests
	mux.Handle("/api/", http.StripPrefix("/api", gwmux))

	// Serve Swagger UI
	mux.HandleFunc("/swagger/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/swagger/" {
			http.Redirect(w, r, "/swagger/index.html", http.StatusMovedPermanently)
			return
		}

		filepath := path.Join("dist/swagger-ui", r.URL.Path[len("/swagger/"):])
		content, err := swaggerUI.ReadFile(filepath)
		if err != nil {
			slog.Error("Failed to read swagger-ui file", "url", r.URL.Path, "err", err)
			http.Error(w, "File not found", http.StatusNotFound)
			return
		}

		// Set content type based on file extension
		ext := path.Ext(filepath)
		switch ext {
		case ".html":
			w.Header().Set("Content-Type", "text/html")
		case ".css":
			w.Header().Set("Content-Type", "text/css")
		case ".js":
			w.Header().Set("Content-Type", "application/javascript")
		}
		w.Write(content)
	})

	// Serve OpenAPI spec
	mux.HandleFunc("/openapi.json", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.Write(swaggerDoc)
	})

	// Start HTTP server with the combined mux wrapped in CORS middleware
	slog.Debug("Starting gRPC Gateway HTTP server", "port", cfg.HttpPort)
	err = http.ListenAndServe(cfg.HttpPort, corsMiddleware(mux))
	slog.Error("Unable to start http server", "err", err)
}
