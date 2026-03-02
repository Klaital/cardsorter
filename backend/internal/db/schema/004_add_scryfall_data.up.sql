
CREATE TABLE scryfall_bulk (
    id INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
    scryfall_id BINARY(16) UNIQUE NOT NULL,
    scryfall_type VARCHAR(32) NOT NULL,
    updated_at DATETIME NOT NULL,
    uri VARCHAR(256) NOT NULL,
    size INT NOT NULL,
    download_uri VARCHAR(256) NOT NULL,

    processing_started_at DATETIME,
    processing_completed_at DATETIME,

    INDEX idx_update (updated_at),
    INDEX idx_processing (processing_started_at),
    INDEX idx_scryfall_id (scryfall_id)
);

CREATE TABLE all_cards (
    id BIGINT UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT,
    scryfall_id BINARY(16) UNIQUE NOT NULL,
    lang VARCHAR(16) NOT NULL,
    layout VARCHAR(32) NOT NULL,
    set_name VARCHAR(8) NOT NULL,
    digital BOOL NOT NULL,
    rarity VARCHAR(16) NOT NULL
);

CREATE TABLE card_faces (
    id BIGINT UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT,
    card_id BIGINT UNSIGNED NOT NULL,
    flavor_text VARCHAR(256),
    layout VARCHAR(32),
    name VARCHAR(128) NOT NULL,
    original_image_uri_png VARCHAR(256),
    original_image_uri_large VARCHAR(256),
    FOREIGN KEY (card_id) REFERENCES all_cards(id)
);

CREATE TABLE card_prices (
    id BIGINT UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT,
    card_id BIGINT UNSIGNED NOT NULL UNIQUE,
    usd INT,
    usd_foil INT,
    usd_etched INT,
    eur INT,
    eur_foil INT,
    tix INT,
    FOREIGN KEY (card_id) REFERENCES all_cards(id)
);