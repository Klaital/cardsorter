// internal/server/auth.go
package server

import (
	"context"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	"log/slog"
)

const (
	deviceSecretHeader = "x-device-secret"
	authTokenHeader    = "authorization"
)

var publicMethods = map[string]bool{
	"/user.v1.UserService/Login": true,
}

var deviceAuthMethods = map[string]bool{
	"/user.v1.UserService/Register": true,
}

func SelectiveAuthInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	slog.Debug("Checking which auth", "method", info.FullMethod)
	// Check if the method requires device authentication
	if deviceAuthMethods[info.FullMethod] {
		if err := validateDeviceAuth(ctx); err != nil {
			return nil, err
		}
	}

	// Check if the method requires authentication
	if !publicMethods[info.FullMethod] {
		// Apply regular user authentication
		return AuthInterceptor(ctx, req, info, handler)
	}

	// Proceed with the handler
	return handler(ctx, req)
}

func validateDeviceAuth(ctx context.Context) error {
	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return status.Error(codes.Unauthenticated, "no metadata provided")
	}

	deviceSecrets := md.Get(deviceSecretHeader)
	if len(deviceSecrets) == 0 {
		return status.Error(codes.Unauthenticated, "device secret required")
	}

	deviceSecret := deviceSecrets[0]
	// TODO: Replace this with your actual device secret validation logic
	if !isValidDeviceSecret(deviceSecret) {
		return status.Error(codes.Unauthenticated, "invalid device secret")
	}

	return nil
}

func isValidDeviceSecret(secret string) bool {
	// TODO: Implement your device secret validation logic
	// This could involve checking against a list of valid device secrets
	// stored in your configuration or database
	return true // Placeholder implementation
}
