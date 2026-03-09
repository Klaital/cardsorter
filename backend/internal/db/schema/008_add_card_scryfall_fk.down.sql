ALTER TABLE cards DROP FOREIGN KEY fk_cards_scryfall_card;
ALTER TABLE cards DROP INDEX idx_cards_scryfall_card;
ALTER TABLE cards DROP COLUMN scryfall_card_id;
DROP INDEX idx_all_cards_set_collector ON all_cards;
