from .bulk_data import Card, Face
import os
import sqlite3

class LocalDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def open(self):
        if not os.path.exists(self.db_path):
            self.create_db()
        else:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

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
              CREATE INDEX idx_setid ON cards (setid, collector_num);
              CREATE INDEX idx_name ON cards (name);
              CREATE INDEX idx_id ON cards (scryfall_id);
              CREATE TABLE faces
              (
                  id             INTEGER PRIMARY KEY,
                  card_id        INTEGER,
                  image_uri_png  TEXT,
                  image_path_png TEXT,
                  face_name      TEXT,
                  image_hash     TEXT
              );
              CREATE INDEX idx_card_id ON faces (card_id);
              CREATE INDEX idx_path ON faces (image_path_png);
              CREATE UNIQUE INDEX idx_face_name ON faces (card_id, face_name);
              ''')
        self.conn.commit()


    def close(self):
        self.conn.close()
        self.cursor = None
        self.conn = None

    def add_card(self, card: Card):
        self.cursor.execute('''
                            INSERT INTO cards (name, scryfall_id, setid, collector_num)
                            VALUES (?, ?, ?, ?)''', (
                                card.name, card.id, card.set_code, card.collector_number
                            ))
        self.conn.commit()

    def add_face(self, face: Face):
        self.cursor.execute('''
            INSERT OR REPLACE INTO faces (card_id, face_name, image_uri_png, image_path_png, image_hash)
            VALUES (?, ?, ?, ?, ?)''', (
            face.card_id, face.face_name, face.image_uris.get("png"), face.local_image_path, face.image_hash
        ))
        self.conn.commit()

    def get_missing_faces(self):
        self.cursor.execute('''SELECT card_id FROM faces WHERE image_hash IS NULL''')
        return self.cursor.fetchall()
