package handlers

import (
	"database/sql"
	"encoding/json"
	"net/http"

	"golang.org/x/crypto/bcrypt"

	"github.com/klaital/cardsorter/backend/internal/auth"
	carddb "github.com/klaital/cardsorter/backend/internal/db"
	"github.com/klaital/cardsorter/backend/internal/models"
)

func Register(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req models.CreateUserRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
		if err != nil {
			http.Error(w, "Error hashing password", http.StatusInternalServerError)
			return
		}

		queries := carddb.New(db)
		result, err := queries.CreateUser(r.Context(), carddb.CreateUserParams{
			Email:        req.Email,
			PasswordHash: string(hashedPassword),
		})
		if err != nil {
			http.Error(w, "Error creating user", http.StatusInternalServerError)
			return
		}

		userID, _ := result.LastInsertId()
		token, err := auth.GenerateToken(userID)
		if err != nil {
			http.Error(w, "Error generating token", http.StatusInternalServerError)
			return
		}

		json.NewEncoder(w).Encode(map[string]string{"token": token})
	}
}

func Login(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req models.LoginRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		queries := carddb.New(db)
		user, err := queries.GetUser(r.Context(), req.Email)
		if err != nil {
			http.Error(w, "Invalid credentials", http.StatusUnauthorized)
			return
		}

		if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password)); err != nil {
			http.Error(w, "Invalid credentials", http.StatusUnauthorized)
			return
		}

		token, err := auth.GenerateToken(user.ID)
		if err != nil {
			http.Error(w, "Error generating token", http.StatusInternalServerError)
			return
		}

		json.NewEncoder(w).Encode(map[string]string{"token": token})
	}
}
