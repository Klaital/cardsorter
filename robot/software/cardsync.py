import logging
import os
import traceback
import argparse
from time import sleep

from scryfall.client import ScryfallClient
from scryfall.bulk_data import Card
from scryfall.localdb import LocalDB

def setup_logging(log_level):
    """Configure logging for the entire application"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('scryfall_downloader.log')  # Optional: also log to file
        ]
    )

if __name__ == '__main__':
    # Load the newest All Cards bulk data from Scryfall.
    # Use the cache file if it's up to date.
    parser = argparse.ArgumentParser(description='Download Magic card images from Scryfall')
    parser.add_argument('--output-dir', default='~/.cardsorter/scryfall/',
                        help='Directory to save downloaded images')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                        help='Enable verbose output')
    parser.add_argument('--card ID', type=str, dest='card_id',
                        help='Download a single card by its Scryfall ID')
    parser.add_argument('--update', action='store_true', dest='update',)
    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    scryfall = ScryfallClient(root_dir=args.output_dir, log_level=log_level)
    cards, isNewData = scryfall.load_all_cards_data()
    logging.info(f"Loaded {len(cards)} cards")
    if isNewData:
        logging.warning("New data downloaded from Scryfall. Please rerun with --update to update the local database and download the new cards' images.")

    logging.info("Opening local database...")
    localdb = LocalDB(os.path.join(args.output_dir, "cards.sqlite3"))
    localdb.open()

    # Update the localdb
    if args.update:
        logging.info("Adding cards to local database...")
        i = 0
        for card in cards:
            i += 1
            if i % 100 == 0:
                print(f"\r{i}", end='')
            localdb.add_card(card)
            for face in card.faces:
                if face.image_uris.get("png") == "https://errors.scryfall.com/soon.jpg":
                    # logging.warning(f"Skipping face on card {card.name} ({card.id}) due to no image on scryfall")
                    continue
                localdb.add_face(face)
                print(".", end='')

    # Look through the localdb for cards that are missing images
    logging.info("Checking for missing cards...")
    missing_cards = localdb.get_missing_faces()
    # If the user requested a specific card, only download that one
    if args.card_id:
        missing_cards = [card for card in missing_cards if card[0] == args.card_id]

    logging.info(f"Downloading {len(missing_cards)} missing cards...")
    for missing_card in missing_cards:
        # Look the card up in the scryfall dataset
        for card in cards:
            if card.id == missing_card[0]:
                logging.info(f"Downloading card {card.name} ({card.id})")
                scryfall.download_card(card)
                # Record the downloaded images in the local database
                for face in card.faces:
                    localdb.upsert_face(face)
                # Wait a bit between downloads so Scryfall isn't getting spammed
                sleep(0.4)
                break