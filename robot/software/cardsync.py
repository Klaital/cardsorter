import logging
import os
import argparse
import time

from scryfall.client import ScryfallClient
from scryfall.localdb import LocalDB
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    try:
        load_dotenv()
        logging.debug("Loaded .env file")
    except Exception as e:
        logging.debug(f"No .env file found or error loading it: {e}")
        # Continue execution as the .env file is optional


def setup_logging(log_level):
    """Configure logging for the entire application"""
    # Get the root logger
    root_logger = logging.getLogger()

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set the logging level
    root_logger.setLevel(log_level)

    # Create and configure handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler('scryfall_downloader.log')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info("Logging configured successfully")

if __name__ == '__main__':
    # Load environment variables from .env file first
    load_environment()
    
    # Load the newest All Cards bulk data from Scryfall.
    # Use the cache file if it's up to date.
    parser = argparse.ArgumentParser(description='Download Magic card images from Scryfall')
    parser.add_argument('--output-dir', default='~/.cardsorter/scryfall/',
                        help='Directory to save downloaded images')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                        help='Enable verbose output')
    parser.add_argument('--card ID', type=str, dest='card_id',
                        help='Download a single card by its Scryfall ID')
    parser.add_argument('--set ID', type=str, dest='set_id',
                        help='Download all cards from a single set')
    parser.add_argument('--update', action='store_true', dest='update',
                        help='Update the local database with new cards')
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
        
        # Start a transaction for bulk operations
        localdb.cursor.execute("BEGIN TRANSACTION")
        
        try:
            for card in cards:
                i += 1
                if i % 1000 == 0:
                    print(f"\r{i}", end='')
                    # Periodic commit to avoid huge transactions
                    localdb.flush_batches()
                    localdb.conn.commit()
                    localdb.cursor.execute("BEGIN TRANSACTION")

                if card.set_code == 'unk': # set "unknown event" usually has no image. Skip it.
                    continue
                # Skip cards that have a missing image
                if card.faces[0].image_uris.get("png") == "https://errors.scryfall.com/soon.jpg":
                    continue

                localdb.add_card(card)

                for face in card.faces:
                    if face.image_uris.get("png") == "https://errors.scryfall.com/soon.jpg":
                        continue
                    localdb.add_face(face)
            
            # Final flush and commit
            localdb.flush_batches()
            localdb.conn.commit()
            
        except Exception as e:
            localdb.conn.rollback()
            raise e
        
        # Flush any remaining telemetry data
        telemetry_batcher.flush()

    # Look through the localdb for cards that are missing images
    logging.info("Checking for missing cards...")
    missing_cards = []
    if args.card_id:
        missing_cards = localdb.get_missing_faces([args.card_id])
    elif args.set_id:
        missing_cards = localdb.get_missing_faces_by_set(args.set_id)
    else:
        # When no specific card or set is specified, process all available sets
        logging.info("No specific card or set specified. Querying for available sets...")
        available_sets = scryfall.list_sets()
        logging.info(f"Found {len(available_sets)} available sets")
        
        # Sort sets by release date (newest first) to prioritize recent sets
        available_sets.sort(key=lambda x: x.get('released_at', ''), reverse=True)
        
        # Process each set iteratively
        for set_info in available_sets:
            set_code = set_info.get('code', '')
            set_name = set_info.get('name', 'Unknown')
            logging.info(f"Processing set: {set_name} ({set_code})")
            
            # Get missing cards for this specific set
            set_missing_cards = localdb.get_missing_faces_by_set(set_code)
            
            if not set_missing_cards:
                logging.info(f"No missing cards found for set {set_name} ({set_code})")
                continue
                
            logging.info(f"Found {len(set_missing_cards)} missing cards in set {set_name} ({set_code})")
            
            # Initialize download tracking for this set
            scryfall.start_download_tracking()
            set_download_start = time.time()

            # Process cards from this set
            for index, missing_card in enumerate(set_missing_cards):
                # Look the card up in the scryfall dataset
                for card in cards:
                    if card.id == missing_card[0]:
                        logging.info(f"Downloading card {card.name} ({card.id}) from {set_name} [{index+1}/{len(set_missing_cards)}]")
                        card_downloaded = scryfall.download_card(card)
                        
                        # if card_downloaded:
                        # Record the downloaded images in the local database
                        for face in card.faces:
                            localdb.upsert_face(face)
                        
                        # Calculate current progress and rates
                        current_elapsed = time.time() - set_download_start
                        current_rate = scryfall.get_download_rate()
                        processed_count = index + 1
                        
                        # Enhanced progress logging
                        progress_percentage = (processed_count / len(set_missing_cards) * 100) if len(set_missing_cards) > 0 else 0
                        remaining_cards = len(set_missing_cards) - processed_count
                        eta_seconds = (remaining_cards / current_rate) if current_rate > 0 else 0
                        eta_minutes = eta_seconds / 60
                        
                        if processed_count % 10 == 0:  # Log detailed progress every 10 cards
                            logging.info(
                                f"Set {set_name} Progress: {processed_count}/{len(set_missing_cards)} ({progress_percentage:.1f}%) "
                                f"Downloaded: {scryfall.downloads_completed} cards "
                                f"Rate: {current_rate:.2f} cards/sec "
                                f"ETA: {eta_minutes:.1f} minutes"
                            )

                        break
            
            # Final set session metrics
            final_set_elapsed = time.time() - set_download_start
            final_set_rate = scryfall.downloads_completed / final_set_elapsed if final_set_elapsed > 0 else 0
            logging.info(f"Completed set {set_name} ({set_code}). Downloaded: {scryfall.downloads_completed} cards in {final_set_elapsed:.1f}s. Average rate: {final_set_rate:.2f} cards/sec")

        # Exit after processing all sets
        logging.info("Finished processing all available sets")
        exit(0)
