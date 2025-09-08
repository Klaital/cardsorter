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
    COALESCE(SUM(c.usd), 0) as total_value
FROM
    libraries l
        LEFT JOIN
    cards c ON l.id = c.library_id
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