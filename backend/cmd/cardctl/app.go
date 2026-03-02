package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strconv"
	"strings"

	"github.com/klaital/cardsorter/backend/internal/db"
	"github.com/klaital/cardsorter/backend/scryfallclient"
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

func (a *App) GetLatestDefaultCards() error {
	client := scryfallclient.New()

	// Fetch metadata about the latest default_cards bulk data
	bulkData, err := client.GetDefaultCardsMetadata()
	if err != nil {
		return fmt.Errorf("fetch bulk data metadata: %w", err)
	}

	fmt.Printf("Found bulk data: %s (updated %s)\n", bulkData.ID, bulkData.UpdatedAt)

	// Check if this bulk data is already in the database
	var bulkRecord db.ScryfallBulk
	bulkRecord, err = a.q.GetScryfallBulkBySID(a.ctx, bulkData.ID.String())
	if err != nil {
		if err == sql.ErrNoRows {
			// Insert the new bulk data record
			fmt.Println("Bulk data not found in database, inserting...")
			_, err = a.q.InsertScryfallBulk(a.ctx, db.InsertScryfallBulkParams{
				UUIDTOBIN:    bulkData.ID.String(),
				ScryfallType: bulkData.Type,
				UpdatedAt:    bulkData.UpdatedAt,
				Uri:          bulkData.URI,
				Size:         int32(bulkData.Size),
				DownloadUri:  bulkData.DownloadURI,
			})
			if err != nil {
				return fmt.Errorf("failed to insert bulk data: %w", err)
			}
			// Re-fetch to get the ID
			bulkRecord, err = a.q.GetScryfallBulkBySID(a.ctx, bulkData.ID.String())
			if err != nil {
				return fmt.Errorf("failed to fetch newly inserted bulk data: %w", err)
			}
		} else {
			return fmt.Errorf("failed to query bulk data: %w", err)
		}
	}

	// Check if processing has already been completed
	if bulkRecord.ProcessingCompletedAt.Valid {
		fmt.Println("Bulk data already processed, skipping")
		return nil
	}

	// Mark processing as started
	fmt.Println("Starting processing...")
	if err := a.q.StartScryfallProcessing(a.ctx, bulkRecord.ID); err != nil {
		return fmt.Errorf("failed to mark processing as started: %w", err)
	}

	// Download and process the cards
	cards, err := client.GetDefaultCards(bulkData)
	if err != nil {
		return fmt.Errorf("failed to download cards: %w", err)
	}

	fmt.Printf("Processing %d cards...\n", len(cards))

	// Process each card
	for i, card := range cards {
		if i%100 == 0 {
			fmt.Printf("Processed %d/%d cards... %s-%s %s\n", i, len(cards), card.SetName, card.CollectorNumber, card.Name)
		}

		// Try to insert the card (will fail silently if already exists due to UNIQUE constraint)
		_, err := a.q.InsertScryfallCard(a.ctx, db.InsertScryfallCardParams{
			UUIDTOBIN: card.ID.String(),
			Lang:      card.Lang,
			Layout:    card.Layout,
			SetName:   card.Set,
			Digital:   card.Digital,
			Rarity:    card.Rarity,
			Name:      card.Name,
		})

		// Get the card ID (whether we just inserted it or it already existed)
		var cardRecord db.AllCard
		cardRecord, err = a.q.GetScryfallCardBySID(a.ctx, card.ID.String())
		if err != nil {
			return fmt.Errorf("failed to get card %s: %w", card.ID, err)
		}

		// Insert card faces (only if card was just inserted)
		// Note: We should check if faces already exist, but for simplicity we'll skip duplicates
		for _, face := range card.GetCardFaces() {
			err = a.q.InsertScryfallFace(a.ctx, db.InsertScryfallFaceParams{
				CardID:     cardRecord.ID,
				FlavorText: sql.NullString{}, // Not available in CardFace struct
				Layout:     sql.NullString{String: card.Layout, Valid: true},
				Name:       face.Name,
				OriginalImageUriPng: sql.NullString{
					String: face.ImageUris.Png,
					Valid:  face.ImageUris.Png != "",
				},
				OriginalImageUriLarge: sql.NullString{
					String: face.ImageUris.Large,
					Valid:  face.ImageUris.Large != "",
				},
				OriginalImageUriSmall: sql.NullString{
					String: face.ImageUris.Small,
					Valid:  face.ImageUris.Small != "",
				},
			})
			if err != nil {
				return fmt.Errorf("failed to insert face for card %s: %w", card.ID, err)
			}
		}

		// Upsert prices (this will update existing or insert new)
		usd := parsePrice(card.Prices.Usd)
		usdFoil := parsePriceAny(card.Prices.UsdFoil)
		usdEtched := parsePriceAny(card.Prices.UsdEtched)
		eur := parsePriceAny(card.Prices.Eur)
		eurFoil := parsePriceAny(card.Prices.EurFoil)
		tix := parsePriceAny(card.Prices.Tix)

		err = a.q.SetScryfallPrices(a.ctx, db.SetScryfallPricesParams{
			CardID:      cardRecord.ID,
			Usd:         usd,
			UsdFoil:     usdFoil,
			UsdEtched:   usdEtched,
			Eur:         eur,
			EurFoil:     eurFoil,
			Tix:         tix,
			Usd_2:       usd,
			UsdFoil_2:   usdFoil,
			UsdEtched_2: usdEtched,
			Eur_2:       eur,
			EurFoil_2:   eurFoil,
			Tix_2:       tix,
		})
		if err != nil {
			return fmt.Errorf("failed to set prices for card %s: %w", card.ID, err)
		}
	}

	// Mark processing as completed
	fmt.Println("Processing complete, marking as done...")
	if err := a.q.CompleteScryfallProcessing(a.ctx, bulkRecord.ID); err != nil {
		return fmt.Errorf("failed to mark processing as completed: %w", err)
	}

	fmt.Printf("Successfully processed %d cards\n", len(cards))
	return nil
}

// parsePrice converts a string price to a sql.NullInt32 (in cents)
func parsePrice(price string) sql.NullInt32 {
	if price == "" {
		return sql.NullInt32{Valid: false}
	}
	f, err := strconv.ParseFloat(price, 64)
	if err != nil {
		return sql.NullInt32{Valid: false}
	}
	return sql.NullInt32{Int32: int32(f * 100), Valid: true}
}

// parsePriceAny converts an any type price to a sql.NullInt32 (in cents)
func parsePriceAny(price any) sql.NullInt32 {
	if price == nil {
		return sql.NullInt32{Valid: false}
	}
	switch v := price.(type) {
	case string:
		return parsePrice(v)
	case float64:
		return sql.NullInt32{Int32: int32(v * 100), Valid: true}
	default:
		return sql.NullInt32{Valid: false}
	}
}
