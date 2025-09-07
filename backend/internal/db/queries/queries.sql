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
SELECT * FROM libraries
WHERE user_id = ?;

-- name: GetLibrary :one
SELECT * FROM libraries
WHERE id = ? AND user_id = ?;

-- name: DeleteLibrary :exec
DELETE FROM libraries
WHERE id = ? AND user_id = ?;

-- name: CreateCard :execresult
INSERT INTO cards (library_id, name, set_name, cnd, foil, collector_num, usd)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- name: GetCards :many
SELECT * FROM cards
WHERE library_id = ?;

-- name: GetCard :one
SELECT * FROM cards
WHERE id = ?;

-- name: MoveCard :exec
UPDATE cards
SET library_id = ?
WHERE id = ?;

-- name: DeleteCard :exec
DELETE FROM cards
WHERE id = ?;