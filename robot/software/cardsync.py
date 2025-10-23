import logging
import os
import traceback
import argparse
from time import sleep
import time

from scryfall.client import ScryfallClient
from scryfall.bulk_data import Card
from scryfall.localdb import LocalDB
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

class TelemetryBatcher:
    def __init__(self, write_api, bucket, batch_size=50):
        self.write_api = write_api
        self.bucket = bucket
        self.batch_size = batch_size
        self.counters = {}
        self.cumulative_counters = {}  # Track cumulative totals
        self.total_count = 0
    
    def increment(self, operation_type="processed"):
        """Increment counter for operation type"""
        if self.write_api is None:
            return
        
        self.counters[operation_type] = self.counters.get(operation_type, 0) + 1
        self.cumulative_counters[operation_type] = self.cumulative_counters.get(operation_type, 0) + 1
        self.total_count += 1
        
        # Flush if we've reached the batch size
        if self.total_count >= self.batch_size:
            self.flush()
    
    def flush(self):
        """Write all accumulated counters to InfluxDB as cumulative totals"""
        if self.write_api is None or not self.counters:
            return
        
        try:
            points = []
            current_time = time.time_ns()
            
            for operation_type, batch_count in self.counters.items():
                # Write cumulative total (for rate calculation)
                cumulative_point = Point("cards_total") \
                    .tag("operation", operation_type) \
                    .field("count", self.cumulative_counters[operation_type]) \
                    .time(current_time)
                points.append(cumulative_point)
                
                # Also write the batch increment (for debugging/monitoring)
                batch_point = Point("cards_batch") \
                    .tag("operation", operation_type) \
                    .field("count", batch_count) \
                    .time(current_time)
                points.append(batch_point)
            
            self.write_api.write(bucket=self.bucket, record=points)
            logging.debug(f"Flushed telemetry batch: {self.counters} (cumulative: {self.cumulative_counters})")
            
            # Reset batch counters but keep cumulative
            self.counters.clear()
            self.total_count = 0
            
        except Exception as e:
            logging.error(f"Failed to write batch to InfluxDB: {e}")

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
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('scryfall_downloader.log')  # Optional: also log to file
        ]
    )

def setup_influxdb():
    """Setup InfluxDB client for telemetry"""
    try:
        # Get InfluxDB configuration from environment variables
        url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        token = os.getenv('INFLUXDB_TOKEN')
        org = os.getenv('INFLUXDB_ORG', 'default')
        bucket = os.getenv('INFLUXDB_BUCKET', 'cardsync')
        
        if not token:
            logging.warning("INFLUXDB_TOKEN not set, telemetry will be disabled")
            return None, None, None
        
        client = InfluxDBClient(url=url, token=token, org=org)
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        logging.info(f"Connected to InfluxDB at {url}")
        return client, write_api, bucket
    except Exception as e:
        logging.error(f"Failed to setup InfluxDB: {e}")
        return None, None, None

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
    parser.add_argument('--update', action='store_true', dest='update',)
    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    # Setup InfluxDB telemetry
    influxdb_client, write_api, bucket = setup_influxdb()
    telemetry_batcher = TelemetryBatcher(write_api, bucket, batch_size=50)

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
                
                localdb.add_card(card)
                telemetry_batcher.increment("added_to_db")
                
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
                telemetry_batcher.increment("downloaded")
                # Record the downloaded images in the local database
                for face in card.faces:
                    localdb.upsert_face(face)
                # Wait a bit between downloads so Scryfall isn't getting spammed
                sleep(0.4)
                break

    # Flush any remaining telemetry data and close InfluxDB client
    telemetry_batcher.flush()
    if influxdb_client:
        influxdb_client.close()