# !/usr/bin/env python3
import time
import sys
import argparse
from PIL import Image
import numpy as np
from scanner.scanner import CardScanner
from picamera2 import Picamera2


def setup_camera(resolution=(1640, 1232)):
    """Initialize and configure the Pi camera."""
    picam = Picamera2()
    config = picam.create_still_configuration(
        main={"size": resolution, "format": "RGB888"},
        lores={"size": (640, 480)},  # Lower resolution stream for preview
        display="lores"
    )
    picam.configure(config)
    picam.start()
    # Give camera time to warm up
    time.sleep(2)
    return picam


def capture_image(picam):
    """Capture an image from the Pi camera."""
    # Capture array and convert to PIL Image
    array = picam.capture_array()
    return Image.fromarray(array)


def print_card_info(card, confidence):
    """Print card information in a formatted way."""
    if not card:
        print("No card detected")
        return

    print("\n=== Card Detection Results ===")
    print(f"Confidence: {confidence:.2f}")
    print(f"Name: {card['name']}")
    print(f"Set: {card.get('set_name', 'Unknown')} ({card.get('set', 'Unknown').upper()})")
    print(f"Collector Number: {card.get('collector_number', 'Unknown')}")

    if 'prices' in card:
        prices = card['prices']
        print("\nPrices:")
        if prices.get('usd'):
            print(f"  USD: ${prices['usd']}")
        if prices.get('usd_foil'):
            print(f"  USD Foil: ${prices['usd_foil']}")
        if prices.get('eur'):
            print(f"  EUR: €{prices['eur']}")
    print("===========================\n")


def main():
    parser = argparse.ArgumentParser(description='Magic: The Gathering card scanner for Raspberry Pi')
    parser.add_argument('--continuous', '-c', action='store_true',
                        help='Run in continuous mode, scanning every few seconds')
    parser.add_argument('--delay', '-d', type=float, default=2.0,
                        help='Delay between scans in continuous mode (seconds)')
    parser.add_argument('--save', '-s', action='store_true',
                        help='Save captured images (debug mode)')
    args = parser.parse_args()

    try:
        print("Initializing camera...")
        picam = setup_camera()
        scanner = CardScanner()

        if args.continuous:
            print("Starting continuous scan mode. Press Ctrl+C to exit.")
            print("Place a card in view of the camera...")

            try:
                while True:
                    image = capture_image(picam)

                    if args.save:
                        image.save('captured.jpg')

                    card, confidence = scanner.detect_card(image)
                    print_card_info(card, confidence)

                    time.sleep(args.delay)
                    print("\nReady for next card...")

            except KeyboardInterrupt:
                print("\nStopping continuous scan mode.")

        else:
            print("Capturing single image...")
            image = capture_image(picam)

            if args.save:
                image.save('captured.jpg')

            card, confidence = scanner.detect_card(image)
            print_card_info(card, confidence)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        if 'picam' in locals():
            picam.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())