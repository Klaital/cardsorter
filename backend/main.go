package main

import (
	"context"
	"database/sql"
	"fmt"
	"github.com/grpc-ecosystem/grpc-gateway/v2/runtime"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"log"
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
	// In production, use environment variables for these values
	db, err := sql.Open("mysql", "af_gil:&jMEa6xYlLVLRApdFgIfJ@tcp(mysql.abandonedfactory.net:3306)/gilgamesh_test?parseTime=true")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatal(err)
	}

	//router := api.NewRouter(db)

	httpPort := os.Getenv("HTTP_PORT")
	if httpPort == "" {
		httpPort = "8080"
	}

	//log.Printf("Server starting on port %s", port)
	//log.Fatal(http.ListenAndServe(":"+port, router))

	// Create a gRPC server
	grpcServer := grpc.NewServer(
		grpc.UnaryInterceptor(server.AuthInterceptor),
	)
	libraryServer := server.NewLibraryServer(db)
	pb.RegisterLibraryServiceServer(grpcServer, libraryServer)

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
