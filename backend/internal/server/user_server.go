package server

import (
	"context"
	"database/sql"
	"errors"
	pb "github.com/klaital/cardsorter/backend/gen/protos"
	"github.com/klaital/cardsorter/backend/internal/auth"
	carddb "github.com/klaital/cardsorter/backend/internal/db"
	"golang.org/x/crypto/bcrypt"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type UserServer struct {
	pb.UnimplementedUserServiceServer
	db *sql.DB
}

func NewUserServer(db *sql.DB) *UserServer {
	return &UserServer{db: db}
}

func (s *UserServer) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.CreateUserResponse, error) {
	if req.Email == "" || req.Password == "" {
		return nil, status.Error(codes.InvalidArgument, "email and password are required")
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to hash password")
	}

	queries := carddb.New(s.db)
	result, err := queries.CreateUser(ctx, carddb.CreateUserParams{
		Email:        req.Email,
		PasswordHash: string(hashedPassword),
	})
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to create user")
	}

	userID, err := result.LastInsertId()
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to get created user ID")
	}

	// Generate JWT token
	token, err := auth.GenerateToken(userID)
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to generate token")
	}

	return &pb.CreateUserResponse{
		Id:    userID,
		Token: token,
	}, nil
}

func (s *UserServer) Login(ctx context.Context, req *pb.LoginRequest) (*pb.LoginResponse, error) {
	if req.Email == "" || req.Password == "" {
		return nil, status.Error(codes.InvalidArgument, "email and password are required")
	}

	queries := carddb.New(s.db)
	user, err := queries.GetUser(ctx, req.Email)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, status.Error(codes.NotFound, "user not found")
		}
		return nil, status.Error(codes.Internal, "failed to fetch user")
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
		return nil, status.Error(codes.Unauthenticated, "invalid password")
	}

	// Generate JWT token
	token, err := auth.GenerateToken(user.ID)
	if err != nil {
		return nil, status.Error(codes.Internal, "failed to generate token")
	}

	return &pb.LoginResponse{
		UserId: user.ID,
		Token:  token,
	}, nil
}
