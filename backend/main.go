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
	"log/slog"
	"net"
	"net/http"
	"os"
	"path"

	_ "github.com/go-sql-driver/mysql"
	pb "github.com/klaital/cardsorter/backend/gen/protos"
	"github.com/klaital/cardsorter/backend/internal/server"
)

//go:embed dist/swagger-ui/*
var swaggerUI embed.FS

//go:embed gen/openapiv2/openapi.swagger.json
var swaggerDoc []byte

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
		slog.Error("failed the initial db ping", "err", err, "connstring", cfg.MysqlDbStringRedacted())
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
	lis, _ := net.Listen("tcp", cfg.GrpcPort)
	go grpcServer.Serve(lis)

	// Create gRPC-Gateway mux
	gwmux := runtime.NewServeMux()
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	err = pb.RegisterLibraryServiceHandlerFromEndpoint(context.Background(), gwmux, "localhost:9090", opts)
	if err != nil {
		slog.Error("Failed to register grpc service", "err", err.Error())
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

	// Start HTTP server with the combined mux
	slog.Debug("Starting gRPC Gateway HTTP server", "port", cfg.HttpPort)
	err = http.ListenAndServe(cfg.HttpPort, mux)
	slog.Error("Unable to start http server", "err", err)
}
