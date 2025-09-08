package server

import (
	"context"
	"database/sql"
	"errors"
	pb "github.com/klaital/cardsorter/backend/gen/protos"
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
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, status.Error(codes.Unauthenticated, "user not authenticated")
	}

	queries := carddb.New(s.db)
	result, err := queries.CreateLibrary(ctx, carddb.CreateLibraryParams{
		UserID: userID,
		Name:   req.Name,
	})
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to create library")
	}

	libraryID, err := result.LastInsertId()
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to get created library ID")
	}

	return &pb.CreateLibraryResponse{
		Id: libraryID,
	}, nil
}

func (s *LibraryServer) GetLibraries(ctx context.Context, req *pb.GetLibrariesRequest) (*pb.GetLibrariesResponse, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, status.Error(codes.Unauthenticated, "user not authenticated")
	}

	queries := carddb.New(s.db)
	libraries, err := queries.GetLibraries(ctx, userID)
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to fetch libraries")
	}

	response := &pb.GetLibrariesResponse{
		Libraries: make([]*pb.Library, 0, len(libraries)),
	}

	for _, lib := range libraries {
		response.Libraries = append(response.Libraries, &pb.Library{
			Id:     lib.ID,
			Name:   lib.Name,
			UserId: lib.UserID,
		})
	}

	return response, nil
}

func (s *LibraryServer) GetLibrary(ctx context.Context, req *pb.GetLibraryRequest) (*pb.GetLibraryResponse, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, status.Error(codes.Unauthenticated, "user not authenticated")
	}

	queries := carddb.New(s.db)
	library, err := queries.GetLibrary(ctx, carddb.GetLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, status.Error(codes.NotFound, "library not found")
		}
		return nil, status.Error(codes.Internal, "failed to fetch library")
	}

	return &pb.GetLibraryResponse{
		Library: &pb.Library{
			Id:     library.ID,
			Name:   library.Name,
			UserId: library.UserID,
		},
	}, nil
}

func (s *LibraryServer) DeleteLibrary(ctx context.Context, req *pb.DeleteLibraryRequest) (*emptypb.Empty, error) {
	userID, err := getUserIDFromContext(ctx)
	if err != nil {
		return nil, status.Error(codes.Unauthenticated, "user not authenticated")
	}

	queries := carddb.New(s.db)
	err = queries.DeleteLibrary(ctx, carddb.DeleteLibraryParams{
		ID:     req.LibraryId,
		UserID: userID,
	})
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "library not found")
		}
		return nil, status.Error(codes.Internal, "failed to delete library")
	}

	return &emptypb.Empty{}, nil
}

// Helper function to get user ID from context
func getUserIDFromContext(ctx context.Context) (int64, error) {
	// This implementation will depend on how you're storing the user ID in the context
	// You might want to define your own context key type
	type userIDKey struct{}

	if userID, ok := ctx.Value(userIDKey{}).(int64); ok {
		return userID, nil
	}
	return 0, status.Error(codes.Unauthenticated, "user ID not found in context")
}
