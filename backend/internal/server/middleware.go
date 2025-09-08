package server

import (
	"context"
	"strings"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

type userIDKey struct{}

// getUserIDFromContext is a helper function to get user ID from context
func getUserIDFromContext(ctx context.Context) (int64, error) {
	// This implementation will depend on how you're storing the user ID in the context
	// You might want to define your own context key type

	if userID, ok := ctx.Value(userIDKey{}).(int64); ok {
		return userID, nil
	}
	return 0, status.Error(codes.Unauthenticated, "user ID not found in context")
}

func AuthInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return nil, status.Error(codes.Unauthenticated, "missing metadata")
	}

	authHeader := md.Get("authorization")
	if len(authHeader) == 0 {
		return nil, status.Error(codes.Unauthenticated, "missing authorization header")
	}

	token := strings.TrimPrefix(authHeader[0], "Bearer ")

	// Here you would validate the token and get the user ID
	userID, err := validateTokenAndGetUserID(token)
	if err != nil {
		return nil, status.Error(codes.Unauthenticated, "invalid token")
	}

	// Create new context with user ID
	newCtx := context.WithValue(ctx, userIDKey{}, userID)

	return handler(newCtx, req)
}

// You'll need to implement this based on your authentication system
func validateTokenAndGetUserID(token string) (int64, error) {
	// Implement your token validation logic here
	return 0, nil
}
