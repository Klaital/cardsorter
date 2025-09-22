import cv2
import numpy as np
from PIL import Image
import pytesseract
import json
import os
from typing import Optional, Dict, Any, Tuple
from util import card_key

class CardScanner:
    def __init__(self, cards_path: str = None):
        """Initialize the card scanner with a path to the cards database."""
        if cards_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            cards_path = os.path.join(current_dir, 'cards.json')

        with open(cards_path, 'r', encoding='utf-8') as f:
            cards_raw = json.load(f)
            self.cards_db = {}
            for card in cards_raw:
                key = card_key(card)
                self.cards_db[key] = card

        # Configure Tesseract
        self.configure_tesseract()

    def configure_tesseract(self):
        """Configure Tesseract OCR settings for optimal card text recognition."""
        custom_config = r'--oem 3 --psm 6'
        pytesseract.pytesseract.config = custom_config

    def find_card_contour(self, image_array: np.ndarray) -> Optional[np.ndarray]:
        """Find the contour of the card in the image.
        
        Args:
            image_array: numpy array of the image
            
        Returns:
            numpy array of contour points or None if no card found
        """
        # Convert to grayscale if needed
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11, 2
        )

        # Find contours
        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        # Find the largest contour by area
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Check if the contour is large enough (at least 10% of image area)
        image_area = gray.shape[0] * gray.shape[1]
        contour_area = cv2.contourArea(largest_contour)
        if contour_area < (image_area * 0.1):
            return None

        # Approximate the contour to a polygon
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        # Check if the polygon has 4 points (rectangle)
        if len(approx) == 4:
            return approx
        return None

    def order_points(self, points: np.ndarray) -> np.ndarray:
        """Order points in clockwise order starting from top-left."""
        rect = np.zeros((4, 2), dtype=np.float32)

        # Find top-left and bottom-right
        s = points.sum(axis=1)
        rect[0] = points[np.argmin(s)]  # Top-left
        rect[2] = points[np.argmax(s)]  # Bottom-right

        # Find top-right and bottom-left
        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]  # Top-right
        rect[3] = points[np.argmax(diff)]  # Bottom-left

        return rect

    def four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> np.ndarray:
        """Apply perspective transform to obtain a top-down view of the card."""
        rect = self.order_points(pts.reshape(4, 2))
        
        # Magic card dimensions (63mm x 88mm)
        width = 640  # Scaled dimensions while maintaining aspect ratio
        height = int(width * (88/63))
        
        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)

        # Calculate perspective transform matrix
        M = cv2.getPerspectiveTransform(rect, dst)
        
        # Apply perspective transformation
        warped = cv2.warpPerspective(image, M, (width, height))
        
        return warped

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess the image for better OCR results.
        
        Args:
            image: PIL Image to preprocess
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert PIL Image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Rotate image 90 degrees clockwise
        cv_image = cv2.rotate(cv_image, cv2.ROTATE_90_CLOCKWISE)
        
        # Find card contour
        contour = self.find_card_contour(cv_image)
        
        if contour is not None:
            # Apply perspective transform to get straight card
            warped = self.four_point_transform(cv_image, contour)
            
            # Convert to grayscale
            gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
            
            # Save the full card detection result
            cv2.imwrite('card_detected.jpg', warped)
        else:
            # If no contour found, just convert rotated image to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        cv2.imwrite('grayscale.jpg', gray)
        # Get dimensions for bottom-left crop
        height, width = gray.shape
        bottom_height = int(height * 0.07)  # 7% of height
        half_width = width // 2
        
        # Crop to bottom-left corner
        cropped = gray[height - bottom_height:height, 0:half_width]
        
        # Save the cropped corner for debugging
        cv2.imwrite('cropped_bottom_left.jpg', cropped)
        
        # Convert back to PIL Image
        image = Image.fromarray(cropped)
        
        # Increase contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Save final preprocessed result
        image.save('preprocessed.jpg')

        return image

    def detect_card(self, image: Image.Image) -> Tuple[Optional[Dict[str, Any]], float]:
        """Detect a Magic: The Gathering card in the image.

        Args:
            image: PIL Image containing the card title

        Returns:
            Tuple of (card_info, confidence) where:
                card_info: Dictionary containing card information or None if no match
                confidence: Float between 0 and 1 indicating match confidence
        """
        # Preprocess the image
        processed = self.preprocess_image(image)
        
        # Extract text using OCR with specific configuration for numbers
        config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        text = pytesseract.image_to_string(processed, config=config)
        
        # Clean up the extracted text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return None, 0.0

        # Debug print
        print(f"OCR Result: {lines}")
        
        # Try to identify set code and collector number
        set_code = None
        collector_number = None
        
        for line in lines:
            # Split the line into parts
            parts = line.split()
            for part in parts:
                # Set codes are typically 3-4 uppercase letters
                if len(part) in [3, 4] and part.isupper():
                    set_code = part
                # Collector numbers are typically 1-3 digits, possibly followed by a letter
                elif part.replace('/', '').isalnum() and any(c.isdigit() for c in part):
                    collector_number = part

        if set_code and collector_number:
            print(f"Found set: {set_code}, number: {collector_number}")
            
            # Try to find the card in the database
            key = f"{set_code.lower()}-{collector_number}"
            card_info = self.cards_db.get(key)
            
            if card_info:
                # Calculate confidence based on exact match
                confidence = 1.0
                return card_info, confidence
    
        return None, 0.0
