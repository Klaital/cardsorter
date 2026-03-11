# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Magic: The Gathering card collection management backend written in Go. It integrates with the Scryfall API to maintain a local database of card data, pricing, and imagery. Users can create libraries to track their card collections with automatic pricing updates.

## Architecture

### Database Layer (sqlc + golang-migrate)

**Type-safe SQL with sqlc**: All database queries are written in SQL files under `internal/db/queries/` and compiled to type-safe Go code using sqlc. The generated code is in `internal/db/`.

- `queries.sql` - User library and card collection queries
- `scryfall.sql` - Scryfall bulk data and card metadata queries

**Schema management**: Database migrations live in `internal/db/schema/` with numbered `.up.sql` and `.down.sql` files. Currently at migration 008.

**Key tables**:
- `users`, `libraries`, `cards` - User collections
- `scryfall_bulk` - Tracks bulk data downloads and processing status
- `all_cards` - Scryfall card metadata (name, set, collector number, rarity)
- `card_faces` - Card face data with image URIs (small/large/PNG for thumbnails and downloads)
- `card_prices` - Pricing data (USD, EUR, foil variants)

**Foreign key relationship**: User `cards` table has a nullable `scryfall_card_id` foreign key to `all_cards`, enabling joins for names, rarity, and conditional price selection (foil vs non-foil).

### Scryfall Integration

The `scryfallclient` package handles Scryfall API interactions:

- **Bulk data downloads**: Uses Scryfall's bulk data API with local file caching
- **HTTP headers**: Always sets `User-Agent: AbandonedCardSorter/1.0` and `Accept: application/json` as required by Scryfall
- **Rate limiting**: No explicit rate limiting needed for bulk data endpoints
- **Processing tracking**: Uses `processing_started_at` and `processing_completed_at` timestamps to prevent duplicate processing

### Performance Optimization

**Transaction batching**: Card processing uses batches of 1000 cards per transaction to minimize network latency to remote MySQL server. This reduces ~400k individual operations to ~400 transaction commits for a full bulk data import.

**Timing instrumentation**: Processing includes detailed timing metrics (begin/process/commit per batch) to identify bottlenecks.

**LastInsertId optimization**: New card inserts use `LastInsertId()` instead of separate SELECT queries to get IDs.

### CLI Tool (cardctl)

Located in `cmd/cardctl/`, this is the primary interface for database management:

**Commands** (kong-based CLI):
- `card list <library-id>` - List cards in a library
- `card add -l <lib> --set <SET> -n <number>` - Add card to library
- `library create <name>` - Create new library
- `library list` - List all libraries
- `scryfall update` - Download and process latest Scryfall bulk data
- `scryfall backfill-numbers <cache-file>` - Backfill collector numbers from cached JSON

**App structure**: Commands delegate to `App` methods in `app.go` which use the sqlc-generated `Querier` interface.

## Development Commands

### Database Operations

Generate Go code from SQL queries (after modifying `internal/db/queries/*.sql`):
```bash
sqlc generate
```

Run migrations (requires `.env` file with DB credentials):
```bash
migrate -path internal/db/schema -database "mysql://${DB_USER}:${DB_PASS}@tcp(${DB_HOST}:3306)/gilgamesh_test" up
```

Or use the Makefile (loads env vars):
```bash
make migrate
```

### Building

Build the CLI tool:
```bash
go build -o cardctl.exe ./cmd/cardctl
```

Build for Linux deployment:
```bash
GOOS=linux go build -o cardsorter .
```

### Configuration

Environment variables (typically in `.env` file):
- `DB_USER`, `DB_PASS`, `DB_HOST` - MySQL connection (required)
- `DB_NAME` - Database name (default: `gilgamesh_test`)
- `DB_PORT` - MySQL port (default: `3306`)
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARN/ERROR)
- `JWT_KEY` - JWT signing key (for API authentication)
- `HTTP_PORT`, `GRPC_PORT` - Service ports (defaults: `:8080`, `:9090`)

## Working with Database Schema

### Adding Migrations

1. Create numbered migration files in `internal/db/schema/`:
   - `00X_description.up.sql` - Forward migration
   - `00X_description.down.sql` - Rollback migration

2. Run migration: `make migrate` or use migrate CLI

3. If adding columns to queries, update SQL in `internal/db/queries/` then run `sqlc generate`

### Foreign Key Constraints

When adding foreign keys between tables with different signedness (e.g., `BIGINT` vs `BIGINT UNSIGNED`), ensure types match exactly. MySQL errors with "incompatible columns" otherwise.

### Conditional Price Selection

User cards store a `foil` boolean. Queries use `CASE` statements to select the correct price:
```sql
CASE
    WHEN c.foil = TRUE THEN cp.usd_foil
    ELSE cp.usd
END as current_usd_price
```

This pattern is used in `GetCards`, `GetCard`, and `GetLibraries` queries.

## Scryfall Data Processing

The bulk data processing pipeline:
1. Fetch metadata about latest `default_cards` bulk data
2. Check if already processed via `scryfall_bulk` table
3. Download bulk data (cached locally by filename)
4. Process in batched transactions:
   - Insert/update card in `all_cards`
   - Insert card faces with image URIs
   - Upsert prices (handles duplicates with `ON DUPLICATE KEY UPDATE`)
5. Mark as completed in `scryfall_bulk` table

**Error handling**: Processing continues on duplicate card errors (inserts fail silently when card exists, then fetches existing ID).

**Batch size**: 1000 cards per transaction provides good balance of memory usage and commit overhead for remote MySQL.

## Code Generation

This project uses code generation extensively:

- **sqlc**: SQL → type-safe Go (run on schema/query changes)
- **protoc**: Proto definitions → gRPC/Gateway code (if using protobuf APIs)

Always regenerate after modifying source files and commit generated code.
