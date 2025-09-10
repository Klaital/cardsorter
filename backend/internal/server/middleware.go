package server

import (
	"context"
	"github.com/golang-jwt/jwt"
	"github.com/klaital/cardsorter/backend/internal/auth"
	"github.com/klaital/cardsorter/backend/internal/config"
	"log/slog"
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

	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return 0, status.Error(codes.Unauthenticated, "user ID not found in context")
	}
	slog.Debug("Loaded metadata", "raw", md)
	if values, ok := md["authorization"]; ok {
		// Parse the JWT
		claims := &auth.Claims{}
		token, err := jwt.ParseWithClaims(values[0], claims, func(token *jwt.Token) (interface{}, error) {
			return config.ParseEnv().JwtKey, nil
		})

		if err != nil || !token.Valid {
			slog.Error("Failed to parse JWT", "err", err, "valid", token.Valid)
			return 0, status.Error(codes.Internal, "failed to parse JWT")
		}
		
		return claims.UserID, nil
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
