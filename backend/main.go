package main

import (
	"context"
	"database/sql"
	"fmt"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"github.com/klaital/cardsorter/backend/internal/config"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"log/slog"
	"net"
	"net/http"
	"os"

	_ "github.com/go-sql-driver/mysql"
	pb "github.com/klaital/cardsorter/backend/gen/protos"
	//"github.com/klaital/cardsorter/backend/internal/api"
	"github.com/klaital/cardsorter/backend/internal/server"
)

func main() {
	cfg := config.ParseEnv()
	db, err := sql.Open("mysql", cfg.MysqlDbString())
	if err != nil {
		slog.Error("Failed to connect to database", "err", err)
		os.Exit(1)
	}
	defer db.Close()
	if err := db.Ping(); err != nil {
		slog.Error("failed the initial db ping", "err", err)
		// TODO: should we wait/retry here? Do we ever wait for the db to be created?
		os.Exit(1)
	}

	grpcServer := grpc.NewServer(
		grpc.UnaryInterceptor(server.AuthInterceptor),
	)

	// Register all services
	pb.RegisterLibraryServiceServer(grpcServer, server.NewLibraryServer(db))
	pb.RegisterUserServiceServer(grpcServer, server.NewUserServer(db))
	pb.RegisterCardServiceServer(grpcServer, server.NewCardServer(db))

	//router := api.NewRouter(db)

	httpPort := os.Getenv("HTTP_PORT")
	if httpPort == "" {
		httpPort = "8080"
	}

	//log.Printf("Server starting on port %s", port)
	//log.Fatal(http.ListenAndServe(":"+port, router))

	// Start gRPC server
	lis, _ := net.Listen("tcp", ":9090")
	go grpcServer.Serve(lis)

	// Create gRPC-Gateway mux
	gwmux := runtime.NewServeMux()
	opts := []grpc.DialOption{grpc.WithTransportCredentials(insecure.NewCredentials())}
	err = pb.RegisterLibraryServiceHandlerFromEndpoint(context.Background(), gwmux, "localhost:9090", opts)
	if err != nil {
		slog.Error("Failed to register grpc service", "err", err.Error())
		os.Exit(1)
	}

	// Start HTTP server
	http.ListenAndServe(fmt.Sprintf(":%s", httpPort), gwmux)

}
