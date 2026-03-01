package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"

	"github.com/klaital/cardsorter/backend/internal/db"
)

type App struct {
	q           db.Querier
	currentUser db.User
	ctx         context.Context
}

func NewApp(q db.Querier, user db.User) *App {
	return &App{
		q:           q,
		currentUser: user,
		ctx:         context.Background(),
	}
}

func (a *App) ListCards(libraryId int64) error {
	lib, err := a.q.GetLibrary(a.ctx, db.GetLibraryParams{
		ID:     libraryId,
		UserID: a.currentUser.ID,
	})
	if err != nil {
		return err
	}

	cards, err := a.q.GetCards(a.ctx, lib.ID)
	if err != nil {
		return err
	}

	for _, card := range cards {
		foilMarker := ""
		if card.Foil.Bool {
			foilMarker = " (F)"
		}
		fmt.Printf("%d\t%d\t%s-%s%s %s\n", card.ID, card.Qty, card.SetName, card.CollectorNum, foilMarker, card.Name)
	}

	return nil
}

func (a *App) AddCard(libraryID int64, set, number, condition string, foil bool) error {
	lib, err := a.q.GetLibrary(a.ctx, db.GetLibraryParams{
		ID:     libraryID,
		UserID: a.currentUser.ID,
	})
	if err != nil {
		return fmt.Errorf("library does not exist")
	}

	_, err = a.q.CreateCard(a.ctx, db.CreateCardParams{
		LibraryID:    lib.ID,
		SetName:      strings.ToUpper(set),
		CollectorNum: number,
		Foil:         sql.NullBool{Bool: foil, Valid: true},
		Cnd:          condition,
		Usd:          0,                                 // will be replaced next time the scryfall scanner runs
		Name:         fmt.Sprintf("%s-%s", set, number), // will be replaced next time the scryfall scanner runs
	})

	// TODO: detect if card already exists, call IncrementCard()

	return err
}

func (a *App) IncrementCard(cardID int64) error {
	return a.q.IncrementCardCount(a.ctx, cardID)
}

func (a *App) CreateLibrary(name string) error {
	_, err := a.q.CreateLibrary(a.ctx, db.CreateLibraryParams{
		Name:   name,
		UserID: a.currentUser.ID,
	})
	return err
}

func (a *App) ListLibraries() error {
	libs, err := a.q.GetLibraries(a.ctx, a.currentUser.ID)
	if err != nil {
		return err
	}

	for _, lib := range libs {
		fmt.Printf("%d\t%s\t%s\n", lib.ID, lib.Name, lib.TotalValue)
	}

	return nil
}

func (a *App) DeleteLibrary(libraryID int64) error {
	return a.q.DeleteLibrary(a.ctx, db.DeleteLibraryParams{
		ID:     libraryID,
		UserID: a.currentUser.ID,
	})
}

func (a *App) RepriceLibrary(libraryID int64) error {
	// TODO: load scryfall data for each card in library
	return errors.New("not implemented")
}
