import os
import sqlite3
from .bulk_data import Card, Face

class LocalDB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def open(self):
        # Check if the sqlite database exists. If not, create it.
        if not os.path.exists(self.db_path):
            self.create_db()
        else:
            # Open the database
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()
        self.cursor = None
        self.conn = None

    def create_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Create the table
        self.cursor.executescript('''
CREATE TABLE cards
(
    id            INTEGER PRIMARY KEY,
    name          TEXT,
    scryfall_id   TEXT,
    setid         TEXT,
    collector_num TEXT
);
CREATE INDEX idx_setid ON cards(setid, collector_num);
CREATE INDEX idx_name ON cards(name);
CREATE INDEX idx_id ON cards(scryfall_id);
CREATE TABLE faces 
(
    id             INTEGER PRIMARY KEY,
    card_id        INTEGER,
    image_uri_png  TEXT,
    image_path_png TEXT,
    face_name      TEXT,
    image_hash     TEXT
);
CREATE INDEX idx_card_id ON faces(card_id);
CREATE INDEX idx_path ON faces(image_path_png);
''')
        self.conn.commit()

    def add_card(self, card: Card):
        self.cursor.execute('''
            INSERT INTO cards (name, scryfall_id, setid, collector_num) VALUES (?, ?, ?, ?)''', (
                card.name, card.id, card.set_code, card.collector_number
        ))
        self.conn.commit()

    def add_face(self, face: Face):
        self.cursor.execute('''
            INSERT INTO faces (card_id, face_name, image_uri_png, image_path_png, image_hash)
            VALUES (?, ?, ?)''', (
                face.card_id, face.face_name, face.image_uris.get("png"), face.local_image_path, face.image_hash
            ))
