package main

import (
	"database/sql"
	"log"
	"net/http"
	"os"

	_ "github.com/go-sql-driver/mysql"
	"github.com/klaital/cardsorter/backend/internal/api"
)

func main() {
	// In production, use environment variables for these values
	db, err := sql.Open("mysql", "af_gil:&jMEa6xYlLVLRApdFgIfJ@tcp(mysql.abandonedfactory.net:3306)/gilgamesh_test?parseTime=true")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatal(err)
	}

	router := api.NewRouter(db)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Server starting on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, router))
}
