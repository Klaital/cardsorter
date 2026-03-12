package main

import (
	"context"
	"database/sql"
	"fmt"
	"strings"

	"github.com/alecthomas/kong"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
	"log/slog"
	"os"

	"github.com/klaital/cardsorter/backend/internal/config"
	carddb "github.com/klaital/cardsorter/backend/internal/db"
)

var CLI struct {
	Card     CardCmd     `cmd:"" help:"Manage cards"`
	Library  LibraryCmd  `cmd:"" help:"Manage libraries"`
	User     UserCmd     `cmd:"" help:"Manage users"`
	Scryfall ScryfallCmd `cmd:"" help:"Scryfall operations: download new bulk data and ingest it into the database."`
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
// USER
//

type UserCmd struct {
	List           UserListCmd           `cmd:"" help:"List all users"`
	Create         UserCreateCmd         `cmd:"" help:"Create a new user with default library"`
	ChangePassword UserChangePasswordCmd `cmd:"" help:"Change user password"`
}

type UserListCmd struct{}

func (u *UserListCmd) Run(a *App) error {
	return a.ListUsers()
}

type UserCreateCmd struct {
	Email    string `arg:"" help:"User email"`
	Password string `arg:"" help:"Initial password"`
}

func (u *UserCreateCmd) Run(a *App) error {
	return a.CreateUser(u.Email, u.Password)
}

type UserChangePasswordCmd struct {
	Email       string `arg:"" help:"User email"`
	NewPassword string `arg:"" help:"New password"`
}

func (u *UserChangePasswordCmd) Run(a *App) error {
	return a.ChangeUserPassword(u.Email, u.NewPassword)
}

//
// LIBRARY
//

type LibraryCmd struct {
	Create LibraryCreateCmd `cmd:"" help:"Create library"`
	List   LibraryListCmd   `cmd:"" help:"List libraries"`
	Rename LibraryRenameCmd `cmd:"" help:"Rename library"`
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
		slog.Error("failed the initial db ping", "err", err, "connstring", cfg.MysqlDbString())
		// TODO: should we wait/retry here? Do we ever wait for the db to be created?
		os.Exit(1)
	}

	queries := carddb.New(db)

	// For user management commands, we don't need a current user
	// For other commands, fetch the default user
	var user carddb.User
	if ctx.Command() != "user list" && ctx.Command() != "user create <email> <password>" &&
		!strings.HasPrefix(ctx.Command(), "user change-password") {
		user, err = queries.GetUser(context.Background(), "kenkaku@gmail.com")
		if err != nil {
			slog.Error("Failed to fetch user", "err", err)
			os.Exit(1)
		}
	}

	// Create a new application
	app := NewApp(queries, db, user)

	err = ctx.Run(app)
	ctx.FatalIfErrorf(err)
}
