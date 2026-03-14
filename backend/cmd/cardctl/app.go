package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/klaital/cardsorter/backend/internal/db"
	"github.com/klaital/cardsorter/backend/scryfallclient"
)

type App struct {
	q           db.Querier
	db          *sql.DB
	currentUser db.User
	ctx         context.Context
}

func NewApp(q db.Querier, database *sql.DB, user db.User) *App {
	return &App{
		q:           q,
		db:          database,
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

		// Use scryfall name if available, otherwise fall back to card name
		displayName := card.Name
		if card.ScryfallName.Valid && card.ScryfallName.String != "" {
			displayName = card.ScryfallName.String
		}

		// Format rarity
		rarity := ""
		if card.Rarity.Valid {
			rarity = fmt.Sprintf(" [%s]", card.Rarity.String)
		}

		// Format price
		priceStr := ""
		if card.CurrentUsdPrice != nil {
			// CurrentUsdPrice is in cents as sql.NullInt32
			if priceVal, ok := card.CurrentUsdPrice.(int32); ok {
				priceStr = fmt.Sprintf(" $%.2f", float64(priceVal)/100.0)
			}
		}

		fmt.Printf("%d\t%d\t%s-%s%s %s%s%s\n",
			card.ID, card.Qty, card.SetName, card.CollectorNum, foilMarker, displayName, rarity, priceStr)
	}

	return nil
}

func (a *App) AddCard(libraryID int64, set, number, condition string, foil bool, language string) error {
	lib, err := a.q.GetLibrary(a.ctx, db.GetLibraryParams{
		ID:     libraryID,
		UserID: a.currentUser.ID,
	})
	if err != nil {
		return fmt.Errorf("library does not exist")
	}

	// Look up the scryfall card by set and collector number
	var scryfallCardID sql.NullInt64
	scryfallCard, err := a.q.GetScryfallCardBySetAndNumber(a.ctx, db.GetScryfallCardBySetAndNumberParams{
		SetName:         strings.ToLower(set),
		CollectorNumber: number,
	})
	if err == nil {
		// Found scryfall card, use its ID and name
		scryfallCardID = sql.NullInt64{Int64: int64(scryfallCard.ID), Valid: true}
	} else if err != sql.ErrNoRows {
		// Some other error occurred
		return fmt.Errorf("failed to lookup scryfall card: %w", err)
	}
	// If err == sql.ErrNoRows, scryfallCardID remains NULL

	cardName := fmt.Sprintf("%s-%s", set, number)
	if scryfallCardID.Valid {
		cardName = scryfallCard.Name
	}

	// Force language to uppercase
	language = strings.ToUpper(language)

	result, err := a.q.CreateCard(a.ctx, db.CreateCardParams{
		LibraryID:       lib.ID,
		SetName:         strings.ToUpper(set),
		CollectorNum:    number,
		Foil:            sql.NullBool{Bool: foil, Valid: true},
		Cnd:             condition,
		Usd:             0,
		Name:            cardName,
		ScryfallCardID:  scryfallCardID,
		Comment:         "",
		Language:        language,
	})
	if err != nil {
		return err
	}

	// Get the card ID
	cardID, err := result.LastInsertId()
	if err != nil {
		return fmt.Errorf("failed to get card ID: %w", err)
	}

	// Fetch the card back to display details
	card, err := a.q.GetCard(a.ctx, cardID)
	if err != nil {
		return fmt.Errorf("failed to fetch card details: %w", err)
	}

	// Print card details
	displayName := card.Name
	if card.ScryfallName.Valid && card.ScryfallName.String != "" {
		displayName = card.ScryfallName.String
	}

	rarityStr := "N/A"
	if card.Rarity.Valid {
		rarityStr = card.Rarity.String
	}

	// Format price
	priceStr := "$0.00"
	if card.CurrentUsdPrice != nil {
		if priceVal, ok := card.CurrentUsdPrice.(int32); ok {
			priceStr = fmt.Sprintf("$%.2f", float64(priceVal)/100.0)
		} else if priceVal, ok := card.CurrentUsdPrice.(int64); ok {
			priceStr = fmt.Sprintf("$%.2f", float64(priceVal)/100.0)
		}
	}

	foilMarker := ""
	if card.Foil.Bool {
		foilMarker = " (Foil)"
	}

	fmt.Printf("\nCard added successfully:\n")
	fmt.Printf("  ID:       %d\n", card.ID)
	fmt.Printf("  Name:     %s%s\n", displayName, foilMarker)
	fmt.Printf("  Set:      %s #%s\n", card.SetName, card.CollectorNum)
	fmt.Printf("  Language: %s\n", card.Language)
	fmt.Printf("  Rarity:   %s\n", rarityStr)
	fmt.Printf("  Price:    %s\n", priceStr)
	fmt.Printf("  Library:  %s\n", lib.Name)

	return nil
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
	_, err := a.q.GetCards(a.ctx, libraryID)
	if err != nil {
		return fmt.Errorf("fetching library data: %w", err)
	}

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

	overallStart := time.Now()
	totalBeginTime := time.Duration(0)
	totalProcessTime := time.Duration(0)
	totalCommitTime := time.Duration(0)

	// Process cards in batches using transactions
	const batchSize = 1000
	for batchStart := 0; batchStart < len(cards); batchStart += batchSize {
		batchEnd := batchStart + batchSize
		if batchEnd > len(cards) {
			batchEnd = len(cards)
		}
		batch := cards[batchStart:batchEnd]

		batchStartTime := time.Now()
		fmt.Printf("Processing batch %d-%d of %d cards...\n", batchStart, batchEnd, len(cards))

		// Start a transaction for this batch
		beginStart := time.Now()
		tx, err := a.db.BeginTx(a.ctx, nil)
		if err != nil {
			return fmt.Errorf("failed to begin transaction: %w", err)
		}
		beginDuration := time.Since(beginStart)
		totalBeginTime += beginDuration

		// Create a querier that uses this transaction
		qtx := a.q.(*db.Queries).WithTx(tx)

		// Process each card in the batch within the transaction
		processStart := time.Now()
		err = a.processBatch(qtx, batch)
		processDuration := time.Since(processStart)
		totalProcessTime += processDuration

		if err != nil {
			tx.Rollback()
			return fmt.Errorf("failed to process batch: %w", err)
		}

		// Commit the transaction
		commitStart := time.Now()
		if err := tx.Commit(); err != nil {
			return fmt.Errorf("failed to commit transaction: %w", err)
		}
		commitDuration := time.Since(commitStart)
		totalCommitTime += commitDuration

		batchDuration := time.Since(batchStartTime)
		fmt.Printf("Batch %d-%d complete: begin=%v, process=%v, commit=%v, total=%v\n",
			batchStart, batchEnd, beginDuration, processDuration, commitDuration, batchDuration)
	}

	overallDuration := time.Since(overallStart)
	fmt.Printf("\nTiming summary:\n")
	fmt.Printf("  Total time: %v\n", overallDuration)
	fmt.Printf("  Begin transactions: %v (%.1f%%)\n", totalBeginTime, float64(totalBeginTime)/float64(overallDuration)*100)
	fmt.Printf("  Processing cards: %v (%.1f%%)\n", totalProcessTime, float64(totalProcessTime)/float64(overallDuration)*100)
	fmt.Printf("  Commit transactions: %v (%.1f%%)\n", totalCommitTime, float64(totalCommitTime)/float64(overallDuration)*100)
	fmt.Printf("  Average per batch: %v\n", overallDuration/time.Duration(len(cards)/batchSize+1))

	// Mark processing as completed
	fmt.Println("Processing complete, marking as done...")
	if err := a.q.CompleteScryfallProcessing(a.ctx, bulkRecord.ID); err != nil {
		return fmt.Errorf("failed to mark processing as completed: %w", err)
	}

	fmt.Printf("Successfully processed %d cards\n", len(cards))
	return nil
}

type batchTimings struct {
	insertCardTime   time.Duration
	selectCardTime   time.Duration
	insertFacesTime  time.Duration
	insertPricesTime time.Duration
	cardCount        int
	selectCount      int
}

func (a *App) processBatch(qtx *db.Queries, cards []scryfallclient.CardData) error {
	timings := &batchTimings{}

	for _, card := range cards {
		// Try to insert the card
		insertStart := time.Now()
		result, err := qtx.InsertScryfallCard(a.ctx, db.InsertScryfallCardParams{
			UUIDTOBIN:       card.ID.String(),
			Lang:            card.Lang,
			Layout:          card.Layout,
			SetName:         card.Set,
			Digital:         card.Digital,
			Rarity:          card.Rarity,
			Name:            card.Name,
			CollectorNumber: card.CollectorNumber,
		})
		timings.insertCardTime += time.Since(insertStart)

		// Get the card ID from the insert result or fetch if already exists
		var cardID uint64
		if err != nil {
			// Card already exists due to UNIQUE constraint, fetch its ID
			selectStart := time.Now()
			cardRecord, err := qtx.GetScryfallCardBySID(a.ctx, card.ID.String())
			timings.selectCardTime += time.Since(selectStart)
			timings.selectCount++

			if err != nil {
				return fmt.Errorf("failed to get existing card %s: %w", card.ID, err)
			}
			cardID = cardRecord.ID
		} else {
			// New card inserted, use LAST_INSERT_ID
			lastID, err := result.LastInsertId()
			if err != nil {
				return fmt.Errorf("failed to get last insert id for card %s: %w", card.ID, err)
			}
			cardID = uint64(lastID)
		}

		// Insert card faces
		for _, face := range card.GetCardFaces() {
			faceStart := time.Now()
			err = qtx.InsertScryfallFace(a.ctx, db.InsertScryfallFaceParams{
				CardID:     cardID,
				FlavorText: sql.NullString{},
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
			timings.insertFacesTime += time.Since(faceStart)

			if err != nil {
				return fmt.Errorf("failed to insert face for card %s: %w", card.ID, err)
			}
		}

		// Upsert prices
		usd := parsePrice(card.Prices.Usd)
		usdFoil := parsePriceAny(card.Prices.UsdFoil)
		usdEtched := parsePriceAny(card.Prices.UsdEtched)
		eur := parsePriceAny(card.Prices.Eur)
		eurFoil := parsePriceAny(card.Prices.EurFoil)
		tix := parsePriceAny(card.Prices.Tix)

		priceStart := time.Now()
		err = qtx.SetScryfallPrices(a.ctx, db.SetScryfallPricesParams{
			CardID:      cardID,
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
		timings.insertPricesTime += time.Since(priceStart)

		if err != nil {
			return fmt.Errorf("failed to set prices for card %s: %w", card.ID, err)
		}

		timings.cardCount++
	}

	// Print timing breakdown for this batch
	totalQueryTime := timings.insertCardTime + timings.selectCardTime + timings.insertFacesTime + timings.insertPricesTime
	fmt.Printf("  Query breakdown: insert_card=%v, select_card=%v (%d selects), insert_faces=%v, insert_prices=%v, total=%v\n",
		timings.insertCardTime, timings.selectCardTime, timings.selectCount,
		timings.insertFacesTime, timings.insertPricesTime, totalQueryTime)

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

func (a *App) BackfillCollectorNumbers(cacheFile string) error {
	// Read the cached JSON file
	file, err := os.Open(cacheFile)
	if err != nil {
		return fmt.Errorf("failed to open cache file: %w", err)
	}
	defer file.Close()

	var cards []scryfallclient.CardData
	if err := json.NewDecoder(file).Decode(&cards); err != nil {
		return fmt.Errorf("failed to decode cards from cache file: %w", err)
	}

	fmt.Printf("Loaded %d cards from cache file, updating collector numbers...\n", len(cards))

	updatedCount := 0
	skippedCount := 0

	// Process in batches using transactions
	const batchSize = 1000
	for batchStart := 0; batchStart < len(cards); batchStart += batchSize {
		batchEnd := batchStart + batchSize
		if batchEnd > len(cards) {
			batchEnd = len(cards)
		}
		batch := cards[batchStart:batchEnd]

		fmt.Printf("Updating batch %d-%d of %d cards...\n", batchStart, batchEnd, len(cards))

		// Start a transaction for this batch
		tx, err := a.db.BeginTx(a.ctx, nil)
		if err != nil {
			return fmt.Errorf("failed to begin transaction: %w", err)
		}

		// Create a querier that uses this transaction
		qtx := a.q.(*db.Queries).WithTx(tx)

		// Update each card in the batch
		for _, card := range batch {
			err := qtx.UpdateCardCollectorNumber(a.ctx, db.UpdateCardCollectorNumberParams{
				CollectorNumber: card.CollectorNumber,
				UUIDTOBIN:       card.ID.String(),
			})
			if err != nil {
				// Card doesn't exist in database, skip it
				skippedCount++
				continue
			}
			updatedCount++
		}

		// Commit the transaction
		if err := tx.Commit(); err != nil {
			return fmt.Errorf("failed to commit transaction: %w", err)
		}

		fmt.Printf("Updated batch %d-%d (updated: %d, skipped: %d so far)\n", batchStart, batchEnd, updatedCount, skippedCount)
	}

	fmt.Printf("Successfully updated collector numbers for %d cards (%d skipped)\n", updatedCount, skippedCount)
	return nil
}
