from scanner import CardScanner
from PIL import Image


def main():
    # Initialize scanner
    scanner = CardScanner()

    # Load test image
    image = Image.open('testdata/spm0082_side1.jpg')

    # Detect card
    card, confidence = scanner.detect_card(image)

    if card:
        print(f"Detected card: {card['name']}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Set: {card.get('set_name', 'Unknown')}")
        print(f"Collector Number: {card.get('collector_number', 'Unknown')}")
        if 'prices' in card:
            print(f"Price (USD): ${card['prices'].get('usd', 'N/A')}")
    else:
        print("No card detected")


if __name__ == "__main__":
    main()