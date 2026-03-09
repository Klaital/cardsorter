package main

import (
	"fmt"
	"os"
)

type ScryfallCmd struct {
	Update          DataUpdateCmd              `cmd:"" help:"Download and ingest new bulk data"`
	BackfillNumbers ScryfallBackfillNumbersCmd `cmd:"" help:"Backfill collector numbers from cached JSON file"`
}

type DataUpdateCmd struct{}

func (d *DataUpdateCmd) Run(a *App) error {
	err := a.GetLatestDefaultCards()
	if err != nil {
		return fmt.Errorf("fetch latest default cards: %w", err)
	}

	os.Exit(1)
	return nil
}

type ScryfallBackfillNumbersCmd struct {
	CacheFile string `arg:"" help:"Path to the cached JSON file" type:"path"`
}

func (s *ScryfallBackfillNumbersCmd) Run(a *App) error {
	return a.BackfillCollectorNumbers(s.CacheFile)
}
