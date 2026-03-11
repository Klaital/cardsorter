package main

import (
	"database/sql"
	"fmt"

	"github.com/klaital/cardsorter/backend/internal/db"
	"golang.org/x/crypto/bcrypt"
)

func (a *App) ListUsers() error {
	// Use a raw query since there's no sqlc query for this yet
	rows, err := a.db.QueryContext(a.ctx, "SELECT id, email, created_at FROM users ORDER BY created_at DESC")
	if err != nil {
		return fmt.Errorf("failed to query users: %w", err)
	}
	defer rows.Close()

	fmt.Println("ID\tEmail\t\t\t\tCreated At")
	fmt.Println("--\t-----\t\t\t\t----------")

	for rows.Next() {
		var id int64
		var email string
		var createdAt sql.NullTime
		if err := rows.Scan(&id, &email, &createdAt); err != nil {
			return fmt.Errorf("failed to scan user row: %w", err)
		}

		createdAtStr := "N/A"
		if createdAt.Valid {
			createdAtStr = createdAt.Time.Format("2006-01-02")
		}

		fmt.Printf("%d\t%-30s\t%s\n", id, email, createdAtStr)
	}

	return rows.Err()
}

func (a *App) CreateUser(email, password string) error {
	// Hash the password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}

	// Create the user
	result, err := a.q.CreateUser(a.ctx, db.CreateUserParams{
		Email:        email,
		PasswordHash: string(hashedPassword),
	})
	if err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}

	userID, err := result.LastInsertId()
	if err != nil {
		return fmt.Errorf("failed to get user ID: %w", err)
	}

	fmt.Printf("Created user %s (ID: %d)\n", email, userID)

	// Create a default library for the user
	libraryResult, err := a.q.CreateLibrary(a.ctx, db.CreateLibraryParams{
		UserID: userID,
		Name:   "My Collection",
	})
	if err != nil {
		return fmt.Errorf("failed to create default library: %w", err)
	}

	libraryID, err := libraryResult.LastInsertId()
	if err != nil {
		return fmt.Errorf("failed to get library ID: %w", err)
	}

	fmt.Printf("Created default library 'My Collection' (ID: %d)\n", libraryID)

	return nil
}

func (a *App) ChangeUserPassword(email, newPassword string) error {
	// Get the user first to verify they exist
	user, err := a.q.GetUser(a.ctx, email)
	if err != nil {
		if err == sql.ErrNoRows {
			return fmt.Errorf("user %s not found", email)
		}
		return fmt.Errorf("failed to get user: %w", err)
	}

	// Hash the new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("failed to hash password: %w", err)
	}

	// Update the password
	_, err = a.db.ExecContext(a.ctx, "UPDATE users SET password_hash = ? WHERE id = ?", string(hashedPassword), user.ID)
	if err != nil {
		return fmt.Errorf("failed to update password: %w", err)
	}

	fmt.Printf("Password changed for user %s (ID: %d)\n", email, user.ID)

	return nil
}
