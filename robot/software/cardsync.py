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
        self.gauges = {}  # Track gauge metrics like rates
        self.total_count = 0
        self.last_rate_update = time.time()
        self.rate_update_interval = 2.0  # Update rate every 2 seconds
    
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
    
    def write_gauge(self, metric_name, field_name, value, tags=None):
        """Write a gauge metric (like rate) immediately to InfluxDB"""
        if self.write_api is None:
            return
        
        try:
            point = Point(metric_name).field(field_name, value).time(time.time_ns())
            if tags:
                for tag_key, tag_value in tags.items():
                    point = point.tag(tag_key, tag_value)
            
            self.write_api.write(bucket=self.bucket, record=[point])
            logging.debug(f"Wrote gauge metric {metric_name}.{field_name}: {value}")
        except Exception as e:
            logging.error(f"Failed to write gauge metric to InfluxDB: {e}")
    
    def should_update_rate(self):
        """Check if it's time to update the rate metric"""
        current_time = time.time()
        if current_time - self.last_rate_update >= self.rate_update_interval:
            self.last_rate_update = current_time
            return True
        return False
    
    def write_progress_metrics(self, current_count, total_count, current_rate, elapsed_time):
        """Write comprehensive progress metrics to InfluxDB"""
        if self.write_api is None:
            return
        
        try:
            points = []
            current_time = time.time_ns()
            
            # Progress metrics
            progress_percentage = (current_count / total_count * 100) if total_count > 0 else 0
            remaining_count = max(0, total_count - current_count)
            estimated_time_remaining = (remaining_count / current_rate) if current_rate > 0 else 0
            
            points.append(Point("download_progress")
                         .field("current_count", current_count)
                         .field("total_count", total_count)
                         .field("remaining_count", remaining_count)
                         .field("progress_percentage", progress_percentage)
                         .field("elapsed_seconds", elapsed_time)
                         .field("estimated_remaining_seconds", estimated_time_remaining)
                         .field("download_rate_faces_per_second", float(current_rate))
                         .time(current_time))
            
            self.write_api.write(bucket=self.bucket, record=points)
            logging.debug(f"Wrote progress metrics: {current_count}/{total_count} ({progress_percentage:.1f}%) at {current_rate:.2f} cards/sec")
            
        except Exception as e:
            logging.debug(f"Failed to write progress metrics to InfluxDB: {e}")
    
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
    parser.add_argument('--set ID', type=str, dest='set_id',
                        help='Download all cards from a single set')
    parser.add_argument('--update', action='store_true', dest='update',
                        help='Update the local database with new cards')
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

                if card.set_code == 'unk': # set "unknown event" usually has no image. Skip it.
                    continue
                # Skip cards that have a missing image
                if card.faces[0].image_uris.get("png") == "https://errors.scryfall.com/soon.jpg":
                    continue

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
    missing_cards = []
    if args.card_id:
        missing_cards = localdb.get_missing_faces([args.card_id])
    elif args.set_id:
        missing_cards = localdb.get_missing_faces_by_set(args.set_id)
    else:
        missing_cards = localdb.get_missing_faces()

    total_missing = len(missing_cards)
    logging.info(f"Downloading {total_missing} missing cards...")
    
    # Initialize download tracking for telemetry
    scryfall.start_download_tracking()
    download_session_start = time.time()
    
    # Send initial progress metrics
    if write_api:
        telemetry_batcher.write_progress_metrics(0, total_missing, 0, 0)
    
    for index, missing_card in enumerate(missing_cards):
        # Look the card up in the scryfall dataset
        for card in cards:
            if card.id == missing_card[0]:
                logging.info(f"Downloading card {card.name} ({card.id}) [{index+1}/{total_missing}]")
                card_downloaded = scryfall.download_card(card, telemetry_batcher)
                
                if card_downloaded:
                    # Record the downloaded images in the local database
                    for face in card.faces:
                        localdb.upsert_face(face)
                
                # Calculate current progress and rates
                current_elapsed = time.time() - download_session_start
                current_rate = scryfall.get_download_rate()
                processed_count = index + 1
                
                # Update telemetry with real-time progress
                if telemetry_batcher.should_update_rate():
                    telemetry_batcher.write_progress_metrics(
                        processed_count, total_missing, current_rate, current_elapsed
                    )
                
                # Enhanced progress logging
                progress_percentage = (processed_count / total_missing * 100) if total_missing > 0 else 0
                remaining_cards = total_missing - processed_count
                eta_seconds = (remaining_cards / current_rate) if current_rate > 0 else 0
                eta_minutes = eta_seconds / 60
                
                if processed_count % 10 == 0:  # Log detailed progress every 10 cards
                    logging.info(
                        f"Progress: {processed_count}/{total_missing} ({progress_percentage:.1f}%) "
                        f"Downloaded: {scryfall.downloads_completed} cards "
                        f"Rate: {current_rate:.2f} cards/sec "
                        f"ETA: {eta_minutes:.1f} minutes"
                    )
                
                # Wait a bit between downloads so Scryfall isn't getting spammed
                sleep(0.4)
                break

    # Final download session metrics
    final_elapsed_time = time.time() - download_session_start
    final_rate = scryfall.downloads_completed / final_elapsed_time if final_elapsed_time > 0 else 0
    logging.info(f"Download session completed. Total: {scryfall.downloads_completed} cards in {final_elapsed_time:.1f}s. Average rate: {final_rate:.2f} cards/sec")
    
    # Send final session metrics
    if write_api:
        telemetry_batcher.write_progress_metrics(
            total_missing, total_missing, final_rate, final_elapsed_time
        )
        telemetry_batcher.write_gauge("download_session", "total_processed", total_missing)
        telemetry_batcher.write_gauge("download_session", "total_downloaded", scryfall.downloads_completed)
        telemetry_batcher.write_gauge("download_session", "duration_seconds", final_elapsed_time)
        telemetry_batcher.write_gauge("download_session", "average_rate", final_rate)
        telemetry_batcher.write_gauge("download_session", "success_rate", 
                                    (scryfall.downloads_completed / total_missing * 100) if total_missing > 0 else 0)

    # Flush any remaining telemetry data and close InfluxDB client
    telemetry_batcher.flush()
    if influxdb_client:
        influxdb_client.close()