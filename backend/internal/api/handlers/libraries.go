package handlers

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
	carddb "github.com/klaital/cardsorter/backend/internal/db"
	"github.com/klaital/cardsorter/backend/internal/models"
)

func CreateLibrary(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req models.CreateLibraryRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		userID := r.Context().Value("user_id").(int64)
		queries := carddb.New(db)
		result, err := queries.CreateLibrary(r.Context(), carddb.CreateLibraryParams{
			UserID: userID,
			Name:   req.Name,
		})
		if err != nil {
			http.Error(w, "Error creating library", http.StatusInternalServerError)
			return
		}

		libraryID, _ := result.LastInsertId()
		json.NewEncoder(w).Encode(map[string]int64{"id": libraryID})
	}
}

func GetLibraries(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userID := r.Context().Value("user_id").(int64)
		queries := carddb.New(db)

		libraries, err := queries.GetLibraries(r.Context(), userID)
		if err != nil {
			http.Error(w, "Error fetching libraries", http.StatusInternalServerError)
			return
		}

		json.NewEncoder(w).Encode(libraries)
	}
}

func GetLibrary(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		libraryID, err := strconv.ParseInt(chi.URLParam(r, "libraryID"), 10, 64)
		if err != nil {
			http.Error(w, "Invalid library ID", http.StatusBadRequest)
			return
		}

		userID := r.Context().Value("user_id").(int64)
		queries := carddb.New(db)

		library, err := queries.GetLibrary(r.Context(), carddb.GetLibraryParams{
			ID:     libraryID,
			UserID: userID,
		})
		if err != nil {
			http.Error(w, "Library not found", http.StatusNotFound)
			return
		}

		json.NewEncoder(w).Encode(library)
	}
}

func DeleteLibrary(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		libraryID, err := strconv.ParseInt(chi.URLParam(r, "libraryID"), 10, 64)
		if err != nil {
			http.Error(w, "Invalid library ID", http.StatusBadRequest)
			return
		}

		userID := r.Context().Value("user_id").(int64)
		queries := carddb.New(db)

		err = queries.DeleteLibrary(r.Context(), carddb.DeleteLibraryParams{
			ID:     libraryID,
			UserID: userID,
		})
		if err != nil {
			http.Error(w, "Error deleting library", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}
