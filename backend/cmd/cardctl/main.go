package main

import (
	"context"
	"database/sql"
	"fmt"
	"github.com/alecthomas/kong"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
	"log/slog"
	"os"

	"github.com/klaital/cardsorter/backend/internal/config"
	carddb "github.com/klaital/cardsorter/backend/internal/db"
)

var CLI struct {
	Card    CardCmd    `cmd:"" help:"Manage cards"`
	Library LibraryCmd `cmd:"" help:"Manage libraries"`
	Data    DataCmd    `cmd:"" help:"Database-level operations"`
}

//
// CARD
//

type CardCmd struct {
	List      CardListCmd      `cmd:"" help:"List cards"`
	Add       CardAddCmd       `cmd:"" help:"Add a card"`
	Increment CardIncrementCmd `cmd:"" help:"Increment quantity"`
}

type CardListCmd struct {
	LibraryID int64 `arg:"" help:"Filter by library" required:""`
}

func (c *CardListCmd) Run(a *App) error {
	return a.ListCards(c.LibraryID)
}

type CardAddCmd struct {
	Library   int64  `short:"l" help:"Library name" required:""`
	Set       string `name:"set" help:"Set code (e.g. mid)" required:""`
	Number    string `short:"n" help:"Collector number" required:""`
	Condition string `short:"c" help:"Condition" default:"new"`
	Foil      bool   `help:"Mark as foil"`
}

func (c *CardAddCmd) Run(a *App) error {
	return a.AddCard(c.Library, c.Set, c.Number, c.Condition, c.Foil)
}

type CardIncrementCmd struct {
	CardID int64 `arg:"" help:"Card ID"`
}

func (c *CardIncrementCmd) Run(a *App) error {
	return a.IncrementCard(c.CardID)
}

//
// LIBRARY
//

type LibraryCmd struct {
	Create  LibraryCreateCmd  `cmd:"" help:"Create library"`
	List    LibraryListCmd    `cmd:"" help:"List libraries"`
	Rename  LibraryRenameCmd  `cmd:"" help:"Rename library"`
	Reprice LibraryRepriceCmd `cmd:"" help:"Reprice library"`
}

type LibraryCreateCmd struct {
	Name string `arg:"" help:"Library name"`
}

func (l *LibraryCreateCmd) Run(a *App) error {
	return a.CreateLibrary(l.Name)
}

type LibraryListCmd struct{}

func (l *LibraryListCmd) Run(a *App) error {
	return a.ListLibraries()
}

type LibraryRenameCmd struct {
	OldName string `arg:"" help:"Current name"`
	NewName string `arg:"" help:"New name"`
}

func (l *LibraryRenameCmd) Run(a *App) error {
	fmt.Printf("Renaming library %s -> %s\n", l.OldName, l.NewName)
	fmt.Printf("not implemented yet")
	os.Exit(1)

	//return a.RenameLibrary(l.OldName, l.NewName)
	return nil
}

type LibraryRepriceCmd struct {
	LibraryID int64 `short:"l" arg:"library" help:"Library ID"`
}

func (l *LibraryRepriceCmd) Run(a *App) error {
	return a.RepriceLibrary(l.LibraryID)
}

//
// DATA
//

type DataCmd struct {
	Describe DataDescribeCmd `cmd:"" help:"Describe database state"`
	Update   DataUpdateCmd   `cmd:"" help:"Update metadata"`
}

type DataDescribeCmd struct{}

func (d *DataDescribeCmd) Run(a *App) error {
	fmt.Printf("not implemented yet")
	os.Exit(1)
	return nil
}

type DataUpdateCmd struct{}

func (d *DataUpdateCmd) Run(a *App) error {
	fmt.Printf("not implemented yet")
	os.Exit(1)
	return nil
}

//
// MAIN
//

func main() {
	ctx := kong.Parse(&CLI)

	// Load .env file if it exists
	if err := godotenv.Load(); err != nil {
		slog.Debug("No .env file found or error loading it", "err", err)
		// Continue execution as the .env file is optional
	}

	cfg := config.ParseEnv()
	db, err := sql.Open("mysql", cfg.MysqlDbString())
	if err != nil {
		slog.Error("Failed to connect to database", "err", err, "connstring", cfg.MysqlDbStringRedacted())
		os.Exit(1)
	}
	defer db.Close()
	if err := db.Ping(); err != nil {
		slog.Error("failed the initial db ping", "err", err, "connstring", cfg.MysqlDbStringRedacted())
		// TODO: should we wait/retry here? Do we ever wait for the db to be created?
		os.Exit(1)
	}

	queries := carddb.New(db)
	user, err := queries.GetUser(context.Background(), "kenkaku@gmail.com")
	if err != nil {
		slog.Error("Failed to fetch user", "err", err)
		os.Exit(1)
	}

	// Create a new application
	app := NewApp(queries, user)

	err = ctx.Run(app)
	ctx.FatalIfErrorf(err)
}
