# !/usr/bin/env python3
import logging
import traceback
import argparse
from time import sleep

from scryfall_client import ScryfallClient

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


def main():
    parser = argparse.ArgumentParser(description='Download Magic card images from Scryfall')
    parser.add_argument('--output-dir', default='~/.cardsorter/scryfall/',
                        help='Directory to save downloaded images')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
                        help='Enable verbose output')
    parser.add_argument('--card ID', type=str, dest='card_id',
                        help='Download a single card by its Scryfall ID')
    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    scryfall = ScryfallClient(root_dir=args.output_dir, log_level=log_level)
    print("Loading card data...")
    cards = scryfall.load_all_cards_data()

    # Update the bulk data to see if we need a new version
    try:
        print("Downloading images...")
        for card in cards:
            if args.card_id and card.id != args.card_id:
                continue
            print(f"Downloading {card.id}...")
            scryfall.download_card(card)
            # Wait a bit between downloads so Scryfall isn't getting spammed
            sleep(0.5)
    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
