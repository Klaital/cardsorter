package server

import (
	"context"
	"database/sql"
	pb "github.com/klaital/cardsorter/backend/gen/library/v1"
	carddb "github.com/klaital/cardsorter/backend/internal/db"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/types/known/emptypb"
)

type LibraryServer struct {
	pb.UnimplementedLibraryServiceServer
	db *sql.DB
}

func NewLibraryServer(db *sql.DB) *LibraryServer {
	return &LibraryServer{db: db}
}

func (s *LibraryServer) CreateLibrary(ctx context.Context, req *pb.CreateLibraryRequest) (*pb.CreateLibraryResponse, error) {
	userID := getUserIDFromContext(ctx) // You'll need to implement this
	queries := carddb.New(s.db)

	result, err := queries.CreateLibrary(ctx, carddb.CreateLibraryParams{
		UserID: userID,
		Name:   req.Name,
	})
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to create library")
	}

	libraryID, _ := result.LastInsertId()
	return &pb.CreateLibraryResponse{
		Id: libraryID,
	}, nil
}

// Implement other methods similarly...
