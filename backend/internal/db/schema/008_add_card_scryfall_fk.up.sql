-- Add index on all_cards to optimize lookups by set_name and collector_number
CREATE INDEX idx_all_cards_set_collector ON all_cards(set_name, collector_number);

-- Add foreign key column to cards table
ALTER TABLE cards ADD COLUMN scryfall_card_id BIGINT UNSIGNED;

-- Add foreign key constraint
ALTER TABLE cards ADD CONSTRAINT fk_cards_scryfall_card
    FOREIGN KEY (scryfall_card_id) REFERENCES all_cards(id);

-- Add index for the foreign key
CREATE INDEX idx_cards_scryfall_card ON cards(scryfall_card_id);
