-- name: ListScryfallBulks :many
SELECT * FROM scryfall_bulk;

-- name: GetScryfallBulkByType :many
SELECT * FROM scryfall_bulk WHERE scryfall_type = ?;

-- name: GetScryfallBulkBySID :one
SELECT * FROM scryfall_bulk WHERE scryfall_id = UUID_TO_BIN(?);

-- name: InsertScryfallBulk :execresult
INSERT INTO scryfall_bulk (scryfall_id, scryfall_type, updated_at, uri, size, download_uri)
VALUES (UUID_TO_BIN(?), ?, ?, ?, ?, ?);

-- name: StartScryfallProcessing :exec
UPDATE scryfall_bulk
SET processing_started_at = NOW()
WHERE id = ?;

-- name: CompleteScryfallProcessing :exec
UPDATE scryfall_bulk
SET processing_completed_at = NOW()
WHERE id = ?;

-- name: InsertScryfallCard :execresult
INSERT INTO all_cards (scryfall_id, lang, layout, set_name, digital, rarity, name)
VALUES (UUID_TO_BIN(?), ?, ?, ?, ?, ?, ?);

-- name: InsertScryfallFace :exec
INSERT INTO card_faces (card_id, flavor_text, layout, name, original_image_uri_png, original_image_uri_large, original_image_uri_small)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- name: SetScryfallPrices :exec
INSERT INTO card_prices (card_id, usd, usd_foil, usd_etched, eur, eur_foil, tix)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON DUPLICATE KEY UPDATE
    usd = ?, usd_foil = ?, usd_etched = ?,
    eur = ?, eur_foil = ?,
    tix = ?;

-- name: GetScryfallCardByValue :one
SELECT all_cards.*,
       card_prices.usd, card_prices.usd_foil,
       card_prices.usd_etched, card_prices.eur,
       card_prices.eur_foil, card_prices.tix
FROM all_cards
    LEFT OUTER JOIN card_prices
    ON all_cards.id = card_prices.card_id;

-- name: GetScryfallCardBySID :one
SELECT * FROM all_cards WHERE scryfall_id = UUID_TO_BIN(?);
