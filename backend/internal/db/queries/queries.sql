-- name: CreateUser :execresult
INSERT INTO users (email, password_hash)
VALUES (?, ?);

-- name: GetUser :one
SELECT * FROM users
WHERE email = ? LIMIT 1;

-- name: CreateLibrary :execresult
INSERT INTO libraries (user_id, name)
VALUES (?, ?);

-- name: GetLibraries :many
SELECT
    l.id,
    l.name,
    COALESCE(SUM(
        CASE
            WHEN c.foil = TRUE THEN COALESCE(cp.usd_foil, c.usd)
            ELSE COALESCE(cp.usd, c.usd)
        END * c.qty
    ), 0) as total_value
FROM
    libraries l
        LEFT JOIN cards c ON l.id = c.library_id
        LEFT JOIN all_cards ac ON c.scryfall_card_id = ac.id
        LEFT JOIN card_prices cp ON ac.id = cp.card_id
WHERE l.user_id = ?
GROUP BY
    l.id, l.name
ORDER BY
    l.id;

-- name: GetLibrary :one
SELECT * FROM libraries
WHERE id = ? AND user_id = ?;

-- name: DeleteLibrary :exec
DELETE FROM libraries
WHERE id = ? AND user_id = ? LIMIT 1;

-- name: CreateCard :execresult
INSERT INTO cards (library_id, name, set_name, cnd, foil, collector_num, usd, qty, scryfall_card_id)
VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
ON DUPLICATE KEY UPDATE
    qty = qty + 1;

-- name: GetCards :many
SELECT
    c.*,
    ac.name as scryfall_name,
    ac.rarity,
    CASE
        WHEN c.foil = TRUE THEN cp.usd_foil
        ELSE cp.usd
    END as current_usd_price
FROM cards c
LEFT JOIN all_cards ac ON c.scryfall_card_id = ac.id
LEFT JOIN card_prices cp ON ac.id = cp.card_id
WHERE c.library_id = ?;

-- name: GetCard :one
SELECT
    c.*,
    ac.name as scryfall_name,
    ac.rarity,
    CASE
        WHEN c.foil = TRUE THEN cp.usd_foil
        ELSE cp.usd
    END as current_usd_price
FROM cards c
LEFT JOIN all_cards ac ON c.scryfall_card_id = ac.id
LEFT JOIN card_prices cp ON ac.id = cp.card_id
WHERE c.id = ?;

-- name: MoveCard :exec
UPDATE cards
SET library_id = ?
WHERE id = ?;

-- name: DeleteCard :exec
DELETE FROM cards
WHERE id = ?;

-- name: IncrementCardCount :exec
UPDATE cards
SET qty = qty + 1
WHERE id = ?;

-- name: UpdateCard :exec
UPDATE cards
SET name=?, usd=?
WHERE id=?;
