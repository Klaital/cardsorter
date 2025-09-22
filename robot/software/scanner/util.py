from PIL import Image
import numpy as np

def card_key(card):
    """Generate a unique key for a card."""
    return card['set'] + '-' + card['collector_number']


def enhance_text_regions(image: Image.Image) -> Image.Image:
    """Enhance regions of the image that likely contain text.

    Args:
        image: PIL Image to enhance

    Returns:
        Enhanced PIL Image
    """
    # Convert to numpy array
    img_array = np.array(image)

    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        from PIL import ImageOps
        image = ImageOps.grayscale(image)
        img_array = np.array(image)

    # Apply adaptive thresholding
    from scipy.ndimage import gaussian_filter
    blurred = gaussian_filter(img_array, sigma=2)
    threshold = blurred - 10
    binary = np.where(img_array > threshold, 255, 0)

    return Image.fromarray(binary.astype(np.uint8))


def extract_title_region(image: Image.Image) -> Image.Image:
    """Extract the region of the image likely to contain the card title.

    Args:
        image: PIL Image of the full card

    Returns:
        PIL Image containing just the title region
    """
    # For Magic cards, the title is typically in the top 15% of the card
    width, height = image.size
    title_height = int(height * 0.15)

    # Crop to the top region
    title_region = image.crop((0, 0, width, title_height))

    return title_region


def cleanup_text(text: str) -> str:
    """Clean up OCR text output.

    Args:
        text: Raw text from OCR

    Returns:
        Cleaned text
    """
    # Remove common OCR artifacts
    replacements = {
        '|': 'I',
        'l': 'I',
        '0': 'O',
        '@': 'a',
        '\n': ' ',
        '  ': ' '
    }

    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    return cleaned.strip()