package api

import (
	"database/sql"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/klaital/cardsorter/backend/internal/api/handlers"
	"github.com/klaital/cardsorter/backend/internal/auth"
)

func NewRouter(db *sql.DB) http.Handler {
	r := chi.NewRouter()

	// Middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	// Public routes
	r.Group(func(r chi.Router) {
		r.Post("/register", handlers.Register(db))
		r.Post("/login", handlers.Login(db))
	})

	// Protected routes
	r.Group(func(r chi.Router) {
		r.Use(auth.AuthMiddleware)

		// Libraries
		r.Route("/libraries", func(r chi.Router) {
			r.Post("/", handlers.CreateLibrary(db))
			r.Get("/", handlers.GetLibraries(db))
			r.Get("/{libraryID}", handlers.GetLibrary(db))
			r.Delete("/{libraryID}", handlers.DeleteLibrary(db))
		})

		// Cards
		r.Route("/libraries/{libraryID}/cards", func(r chi.Router) {
			r.Post("/", handlers.CreateCard(db))
			r.Get("/", handlers.GetCards(db))
		})

		r.Route("/cards", func(r chi.Router) {
			r.Get("/{cardID}", handlers.GetCard(db))
			r.Delete("/{cardID}", handlers.DeleteCard(db))
			r.Post("/{cardID}/move", handlers.MoveCard(db))
		})
	})

	return r
}
