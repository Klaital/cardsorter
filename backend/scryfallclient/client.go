package scryfallclient

import (
	"encoding/json"
	"fmt"
	"github.com/google/uuid"
	"io"
	"log/slog"
	"net/http"
	"os"
	"strings"
	"time"
)

type Client struct {
}

func New() *Client {
	return &Client{}
}

type BulkData struct {
	Object          string    `json:"object"`
	ID              uuid.UUID `json:"id"`
	Type            string    `json:"type"`
	UpdatedAt       time.Time `json:"updated_at"`
	URI             string    `json:"uri"`
	Name            string    `json:"name"`
	Description     string    `json:"description"`
	Size            int       `json:"size"`
	DownloadURI     string    `json:"download_uri"`
	ContentType     string    `json:"content_type"`
	ContentEncoding string    `json:"content_encoding"`
}

func (c *Client) GetDefaultCardsMetadata() (*BulkData, error) {
	req, err := http.NewRequest("GET", "https://api.scryfall.com/bulk-data/default_cards", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("User-Agent", "AbandonedCardSorter/1.0")
	req.Header.Set("Accept", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch bulk data: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		slog.Error("Failed to fetch bulk data metadata", "status", resp.StatusCode, "uri", resp.Request.URL.String())
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var bulkData BulkData
	if err := json.NewDecoder(resp.Body).Decode(&bulkData); err != nil {
		return nil, fmt.Errorf("failed to decode bulk data response: %w", err)
	}

	return &bulkData, nil
}

func filepathFromURI(uri string) string {
	// split the URI into path and filename
	tokens := strings.Split(uri, "/")
	return tokens[len(tokens)-1]
}

func (c *Client) GetDefaultCards(source *BulkData) ([]CardData, error) {
	// Check if the file has already been downloaded
	localCachePath := filepathFromURI(source.DownloadURI)
	// Check if the file exists locally
	if _, err := os.Stat(localCachePath); err == nil {
		// File exists, load data from it
		file, err := os.Open(localCachePath)
		if err != nil {
			return nil, fmt.Errorf("failed to open local file: %w", err)
		}
		defer file.Close()

		cardData := []CardData{}
		if err := json.NewDecoder(file).Decode(&cardData); err != nil {
			return nil, fmt.Errorf("failed to decode cards from local file: %w", err)
		}

		return cardData, nil
	}

	req, err := http.NewRequest("GET", source.DownloadURI, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Set("User-Agent", "AbandonedCardSorter/1.0")
	req.Header.Set("Accept", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch default cards: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}
	// Save the response to a file
	file, err := os.Create(localCachePath)
	if err != nil {
		return nil, fmt.Errorf("failed to create local file: %w", err)
	}
	defer file.Close()

	cardData := []CardData{}
	tee := io.TeeReader(resp.Body, file)
	if err := json.NewDecoder(tee).Decode(&cardData); err != nil {
		return nil, fmt.Errorf("failed to decode default cards response: %w", err)
	}
	return cardData, nil
}
