import json
import os
from datetime import datetime
from typing import List

import pytz
from .bulk_data import BulkDataDescription, Card, cards_from_json_array, Face
import requests
import logging

class ScryfallClient:
    def __init__(self, **kwargs):
        root_dir = kwargs.get("root_dir", "~/.cardsorter/")
        self.all_cards_file = os.path.join(root_dir, "all_cards.json")
        self.images_dir = os.path.join(root_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(kwargs.get("log_level", logging.DEBUG))

        # Open the local Card DB sqlite3 database
        # self.db_path = os.path.join(root_dir, "cards.sqlite3")
        # self.db = LocalDB(self.db_path)
        # self.db.open()

    def load_all_cards_data(self) -> (List[Card], bool):
        self.logger.debug("Loading all cards data...")
        all_cards_description = self.get_all_cards_metadata()
        # Check if the bulk data file is up-to-date. If it is, load it from disk
        # If not, download the latest version from Scryfall.
        if os.path.exists(self.all_cards_file):
            last_download_at = os.path.getmtime(self.all_cards_file)
        else:
            self.logger.info(f"All Cards metadata file does not exist. {self.all_cards_file}")
            last_download_at = 0
        last_download_at = pytz.timezone('America/Los_Angeles').localize(datetime.fromtimestamp(last_download_at))
        cards = []
        updated = False
        if all_cards_description.updated_at_datetime > last_download_at:
            self.logger.info(f"Downloading new bulk data from Scryfall. Updated at {all_cards_description.updated_at_datetime}")
            cards = ScryfallClient.get_all_cards_data(all_cards_description.download_uri, self.all_cards_file)
            updated = True
        else:
            self.logger.info(f"Loading card data from cached file {self.all_cards_file}.")
            with open(self.all_cards_file, "r", encoding="utf-8") as f:
                cards = cards_from_json_array(json.load(f))

        self.logger.info(f"Loaded {len(cards)} cards.")
        return cards, updated

    def get_all_cards_metadata(self) -> BulkDataDescription:
        """Fetch the newest version of the All Cards bulk data file from Scryfall."""
        uri = "https://api.scryfall.com/bulk-data/all-cards"
        response = requests.get(uri)
        response.raise_for_status()
        self.logger.debug("Loaded all-cards metadata")
        return BulkDataDescription(**response.json())

    @staticmethod
    def get_all_cards_data(uri: str, cache_file: str = None) -> List[Card]:
        """Download the bulk data update for All Cards from Scryfall."""
        response = requests.get(uri)
        response.raise_for_status()
        if cache_file:
            with open(cache_file, "wb") as f:
                f.write(response.content)
        return response.content

    def download_card(self, card: Card):
        # Ensure the card is in the database
        # self.db.add_card(card)
        for face in card.faces:
            self.download_face(face)

    def download_face(self, face: Face):
        full_path = face.compute_local_image_path(self.images_dir)
        ensure_dir_exists(os.path.dirname(full_path))

        # Check if the card has already been downloaded
        if os.path.exists(full_path):
            # self.db.add_face(face)
            return

        # Check if the card was downloaded previously
        alt_path = face.compute_alt_image_path(self.images_dir)
        if os.path.exists(alt_path):
            self.logger.debug(f"Card face {face.id} image already exists at {alt_path}")
            face.local_image_path = alt_path
            face.image_hash = face.compute_image_hash()
            # self.db.add_face(face)
            return

        image_url = face.image_uris.get("png")
        if image_url:
            self.logger.debug(f"Downloading face {face.name} image to {full_path}")
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(full_path, "wb") as f:
                    f.write(response.content)
                face.local_image_path = full_path
                # Compute a hash for the image
                face.image_hash = face.compute_image_hash()

                # Update the database with this card's data
                # self.db.add_face(face)
                self.logger.debug(
                    f"Card face {face.id} image downloaded and added to database."
                )
            else:
                raise Exception(f"Failed to download card {face.card_id}, face {face.face_name} image: {response.status_code}")

def ensure_dir_exists(path):
    os.makedirs(path, exist_ok=True)