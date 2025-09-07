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

func CreateCard(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		libraryID, err := strconv.ParseInt(chi.URLParam(r, "libraryID"), 10, 64)
		if err != nil {
			http.Error(w, "Invalid library ID", http.StatusBadRequest)
			return
		}

		var req models.CreateCardRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		queries := carddb.New(db)
		result, err := queries.CreateCard(r.Context(), carddb.CreateCardParams{
			LibraryID:    libraryID,
			Name:         req.Name,
			SetName:      req.SetName,
			Cnd:          req.Condition,
			Foil:         sql.NullBool{Bool: req.Foil, Valid: true},
			CollectorNum: req.CollectorNumber,
			Usd:          req.USDPrice,
		})
		if err != nil {
			http.Error(w, "Error creating card", http.StatusInternalServerError)
			return
		}

		cardID, _ := result.LastInsertId()
		json.NewEncoder(w).Encode(map[string]int64{"id": cardID})
	}
}

func GetCards(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		libraryID, err := strconv.ParseInt(chi.URLParam(r, "libraryID"), 10, 64)
		if err != nil {
			http.Error(w, "Invalid library ID", http.StatusBadRequest)
			return
		}

		queries := carddb.New(db)
		cards, err := queries.GetCards(r.Context(), libraryID)
		if err != nil {
			http.Error(w, "Error fetching cards", http.StatusInternalServerError)
			return
		}

		json.NewEncoder(w).Encode(cards)
	}
}

func GetCard(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cardID, err := strconv.ParseInt(chi.URLParam(r, "cardID"), 10, 64)
		if err != nil {
			http.Error(w, "Invalid card ID", http.StatusBadRequest)
			return
		}

		queries := carddb.New(db)
		card, err := queries.GetCard(r.Context(), cardID)
		if err != nil {
			http.Error(w, "Card not found", http.StatusNotFound)
			return
		}

		json.NewEncoder(w).Encode(card)
	}
}

func MoveCard(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cardID, err := strconv.ParseInt(chi.URLParam(r, "cardID"), 10, 64)
		if err != nil {
			http.Error(w, "Invalid card ID", http.StatusBadRequest)
			return
		}

		var req models.MoveCardRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		queries := carddb.New(db)
		err = queries.MoveCard(r.Context(), carddb.MoveCardParams{
			ID:        cardID,
			LibraryID: req.NewLibraryID,
		})
		if err != nil {
			http.Error(w, "Error moving card", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}

func DeleteCard(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cardID, err := strconv.ParseInt(chi.URLParam(r, "cardID"), 10, 64)
		if err != nil {
			http.Error(w, "Invalid card ID", http.StatusBadRequest)
			return
		}

		queries := carddb.New(db)
		err = queries.DeleteCard(r.Context(), cardID)
		if err != nil {
			http.Error(w, "Error deleting card", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}
