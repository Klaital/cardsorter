package main

import (
	"fmt"
	"os"
)

type ScryfallCmd struct {
	Update DataUpdateCmd `cmd:"" help:"Download and ingest new bulk data"`
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
