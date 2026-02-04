from .bulk_data import Card, Face
import os
import sqlite3

class LocalDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._batch_size = 1000
        self._pending_cards = []
        self._pending_faces = []

    def open(self):
        if not os.path.exists(self.db_path):
            self.create_db()
        else:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            # Check if we need to migrate the database
            self._migrate_db()
        
        # Performance optimizations
        self.cursor.execute("PRAGMA journal_mode = WAL")
        self.cursor.execute("PRAGMA synchronous = NORMAL")
        self.cursor.execute("PRAGMA cache_size = 10000")
        self.cursor.execute("PRAGMA temp_store = MEMORY")

    def _migrate_db(self):
        """Check if lang column exists and add it if not"""
        try:
            # Check if lang column exists
            self.cursor.execute("PRAGMA table_info(cards)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'lang' not in columns:
                print("Adding 'lang' column to cards table...")
                self.cursor.execute("ALTER TABLE cards ADD COLUMN lang TEXT DEFAULT 'en'")
                self.conn.commit()
                print("Database migration completed.")
        except sqlite3.Error as e:
            print(f"Error during database migration: {e}")

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
                  collector_num TEXT,
                  lang          TEXT DEFAULT 'en'
              );
              CREATE INDEX idx_setid ON cards (setid, collector_num);
              CREATE INDEX idx_name ON cards (name);
              CREATE INDEX idx_id ON cards (scryfall_id);
              CREATE INDEX idx_lang ON cards (lang);
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
        # Flush any pending batches before closing
        self.flush_batches()
        if self.conn:
            self.conn.close()
        self.cursor = None
        self.conn = None

    def add_card(self, card: Card):
        # Get language from card object, default to 'en' if not available
        lang = getattr(card, 'lang', 'en')
        self._pending_cards.append((card.name, card.id, card.set_code, card.collector_number, lang))
        
        if len(self._pending_cards) >= self._batch_size:
            self._flush_cards()

    def add_face(self, face: Face):
        self._pending_faces.append((
            face.card_id, face.face_name, face.image_uris.get("png"), 
            face.local_image_path, face.image_hash
        ))
        
        if len(self._pending_faces) >= self._batch_size:
            self._flush_faces()

    def _flush_cards(self):
        if not self._pending_cards:
            return
        
        self.cursor.executemany('''
            INSERT INTO cards (name, scryfall_id, setid, collector_num, lang)
            VALUES (?, ?, ?, ?, ?)''', self._pending_cards)
        self._pending_cards.clear()

    def _flush_faces(self):
        if not self._pending_faces:
            return
        
        self.cursor.executemany('''
            INSERT OR REPLACE INTO faces (card_id, face_name, image_uri_png, image_path_png, image_hash)
            VALUES (?, ?, ?, ?, ?)''', self._pending_faces)
        self._pending_faces.clear()

    def flush_batches(self):
        """Manually flush all pending batches and commit"""
        self._flush_cards()
        self._flush_faces()
        if self.conn:
            self.conn.commit()

    def upsert_face(self, face: Face):
        # For individual upserts (like during downloads), still use immediate execution
        self.cursor.execute('''
            INSERT OR REPLACE INTO faces (card_id, face_name, image_uri_png, image_path_png, image_hash)
            VALUES (?, ?, ?, ?, ?)''', (
            face.card_id, face.face_name, face.image_uris.get("png"), face.local_image_path, face.image_hash
        ))
        self.conn.commit()

    def get_missing_faces(self, scryfall_ids: list[str]=None):
        # Make sure all batches are flushed before querying
        if scryfall_ids is None:
            scryfall_ids = []
        self.flush_batches()
        query = '''SELECT card_id FROM faces WHERE image_hash = ""'''
        if scryfall_ids:
            query += f" AND card_id IN ({','.join(['?'] * len(scryfall_ids))})"
        self.cursor.execute(query, scryfall_ids)
        return self.cursor.fetchall()

    def get_missing_faces_by_set(self, set_id: str):
        # Make sure all batches are flushed before querying
        self.flush_batches()
        query = '''SELECT DISTINCT(cards.scryfall_id) FROM cards JOIN faces ON cards.scryfall_id = faces.card_id WHERE cards.setid = ? AND faces.image_hash = ""'''
        self.cursor.execute(query, (set_id,))
        return self.cursor.fetchall()

    def get_faces_with_download(self):
        # Make sure all batches are flushed before querying
        self.flush_batches()
        query = '''SELECT faces.id, cards.setid FROM faces JOIN cards ON cards.scryfall_id = faces.card_id WHERE faces.image_path_png not LIKE "%set%"'''
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_face(self, face_id) -> Face:
        self.cursor.execute('''
            SELECT id, card_id, face_name, image_uri_png, image_path_png, image_hash FROM faces WHERE id = ?''', (face_id,))
        row = self.cursor.fetchone()
        if row:
            return Face(
                id=row[0],
                card_id=row[1],
                name=row[2],
                image_uris={"png": row[3]},
                local_image_path=row[4],
                image_hash=row[5]
            )
        raise Exception(f"Face {face_id} not found")

    def get_cards_by_language(self, lang: str):
        """Get all cards for a specific language"""
        self.flush_batches()
        query = '''SELECT id, name, scryfall_id, setid, collector_num, lang FROM cards WHERE lang = ?'''
        self.cursor.execute(query, (lang,))
        return self.cursor.fetchall()