import json
import os
from datetime import datetime

import numpy as np
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from PIL import Image as PILImage
from kivy.clock import Clock
from kivy.app import App
import cv2
from scanner.scanner import CardScanner

# Try importing Picamera2 for Raspberry Pi camera support
try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAM_AVAILABLE = True
except ImportError as e:
    print(f"Picamera2 not found. Falling back to regular camera. {e}")
    PICAM_AVAILABLE = False

class CatalogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create directory for saved card images if it doesn't exist
        self.save_directory = "captured_cards"
        os.makedirs(self.save_directory, exist_ok=True)
        
        # Main layout
        self.layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)
        
        # Left side - Text fields and buttons
        left_panel = BoxLayout(orientation='vertical', spacing=10, size_hint=(0.4, 1))
        
        # Library name label
        self.library_label = Label(
            text="Library: None selected",
            font_size=20,
            size_hint=(1, 0.1),
            halign='left'
        )
        self.library_label.bind(size=self.library_label.setter('text_size'))
        left_panel.add_widget(self.library_label)
        
        # Labels for card info
        self.title_label = Label(text="Title: ", font_size=18)
        self.set_label = Label(text="Set: ", font_size=18)
        self.num_label = Label(text="Collector Number: ", font_size=18)
        self.price_label = Label(text="Price: ", font_size=18)
        
        left_panel.add_widget(self.title_label)
        left_panel.add_widget(self.set_label)
        left_panel.add_widget(self.num_label)
        left_panel.add_widget(self.price_label)
        
        # Add spacer to push buttons to bottom
        left_panel.add_widget(BoxLayout(size_hint=(1, 1)))
        
        # Submit + Back buttons
        button_row = BoxLayout(size_hint=(1, 0.2), spacing=10)
        back_btn = Button(text="Back")
        back_btn.bind(on_press=self.go_back)
        button_row.add_widget(back_btn)

        exit_btn = Button(text="Exit")
        exit_btn.bind(on_press=App.get_running_app().stop)
        button_row.add_widget(exit_btn)

        submit_btn = Button(text="Submit")
        submit_btn.bind(on_press=self.submit_action)
        button_row.add_widget(submit_btn)

        left_panel.add_widget(button_row)
        
        # Right side - Camera and preview
        right_panel = BoxLayout(orientation='vertical', size_hint=(0.6, 1), spacing=10)
        
        # Initialize camera
        self.picam = None
        self.setup_camera()
        
        # Card preview window
        preview_container = BoxLayout(orientation='vertical', size_hint=(1, 0.7))
        preview_label = Label(text="Detected Card:", size_hint=(1, 0.1), font_size=16)
        preview_container.add_widget(preview_label)
        
        self.card_preview = Image(size_hint=(1, 0.9))
        preview_container.add_widget(self.card_preview)
        right_panel.add_widget(preview_container)
        
        # Camera view (now at bottom and smaller)
        camera_container = BoxLayout(orientation='vertical', size_hint=(1, 0.3))
        camera_label = Label(text="Camera View:", size_hint=(1, 0.1), font_size=14)
        camera_container.add_widget(camera_label)
        
        camera_view_container = BoxLayout(size_hint=(1, 0.9))
        camera_view_container.add_widget(self.camera)
        camera_container.add_widget(camera_view_container)
        right_panel.add_widget(camera_container)

        # Add panels to main layout
        self.layout.add_widget(left_panel)
        self.layout.add_widget(right_panel)
        
        self.add_widget(self.layout)
        
        # Schedule the preview update
        Clock.schedule_interval(self.update_preview, 1.0/30.0)
        
        # Load card database
        try:
            with open("scanner/cards.json", "r", encoding="utf-8") as f:
                self.cards = json.load(f)
        except FileNotFoundError:
            self.cards = []
        
        self.card_lookup = {}
        for card in self.cards:
            name = card.get("name")
            if name:
                self.card_lookup[name.lower()] = card
        
        # Store the last detected card contour for cropping
        self.last_card_contour = None

    def detect_card_contour(self, pil_image: PILImage.Image):
        """Detect the largest rectangular contour in the image that could be a card.
        
        Args:
            pil_image: PIL Image to process
            
        Returns:
            tuple: (contour, bounding_rect) if card detected, (None, None) otherwise
        """
        # Convert PIL to OpenCV format
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
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
            return None, None
            
        # Filter contours by area and aspect ratio
        image_area = gray.shape[0] * gray.shape[1]
        valid_contours = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Must be at least 5% of image area
            if area < (image_area * 0.05):
                continue
                
            # Approximate the contour to a polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's roughly rectangular (3-6 corners after approximation)
            if len(approx) >= 3 and len(approx) <= 6:
                # Check aspect ratio (cards are roughly 2.5:3.5 ratio)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                
                # Magic cards are typically 2.5" x 3.5", so ratio should be around 0.71
                # Allow some tolerance: 0.5 to 1.0
                if 0.5 <= aspect_ratio <= 1.0:
                    valid_contours.append((contour, area, (x, y, w, h)))
        
        if not valid_contours:
            return None, None
            
        # Return the largest valid contour
        best_contour = max(valid_contours, key=lambda x: x[1])
        return best_contour[0], best_contour[2]

    def order_points(self, pts):
        """Order points for perspective transformation: top-left, top-right, bottom-right, bottom-left"""
        rect = np.zeros((4, 2), dtype="float32")
        
        # Sum and difference to find corners
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        
        # Top-left has smallest sum, bottom-right has largest sum
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right has smallest difference, bottom-left has largest difference
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect

    def crop_card_from_contour(self, pil_image: PILImage.Image, contour):
        """Extract the card region from the image using perspective transformation.
        
        Args:
            pil_image: PIL Image to crop from
            contour: OpenCV contour of the detected card
            
        Returns:
            PIL Image of the cropped and perspective-corrected card, or None if cropping fails
        """
        if contour is None:
            return None
            
        try:
            # Convert PIL to OpenCV
            cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Approximate the contour to get corner points
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # If we have exactly 4 points, use them for perspective transform
            if len(approx) == 4:
                # Reshape and convert to float32
                src_pts = approx.reshape(4, 2).astype("float32")
                
                # Order the points
                src_pts = self.order_points(src_pts)
                
                # Define the dimensions for the output card (much larger)
                # Magic cards are 2.5" x 3.5" (aspect ratio ~0.714)
                card_width = 400  # Increased from 250
                card_height = int(card_width / 0.714)  # ~560
                
                # Define destination points for the perspective transform
                dst_pts = np.array([
                    [0, 0],                           # top-left
                    [card_width - 1, 0],              # top-right
                    [card_width - 1, card_height - 1], # bottom-right
                    [0, card_height - 1]              # bottom-left
                ], dtype="float32")
                
                # Calculate perspective transform matrix
                M = cv2.getPerspectiveTransform(src_pts, dst_pts)
                
                # Apply perspective transform
                warped = cv2.warpPerspective(cv_image, M, (card_width, card_height))
                
                # Convert back to PIL
                warped_pil = PILImage.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
                
                return warped_pil
            
            else:
                # Fall back to bounding rectangle if we don't have exactly 4 corners
                x, y, w, h = cv2.boundingRect(contour)
                
                # Minimal padding (just 2-3 pixels)
                padding = 3
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(pil_image.width - x, w + 2 * padding)
                h = min(pil_image.height - y, h + 2 * padding)
                
                # Crop using bounding rectangle
                cropped = pil_image.crop((x, y, x + w, y + h))
                
                # Resize to larger standard card dimensions while maintaining aspect ratio
                target_width = 400  # Increased from 250
                aspect_ratio = cropped.height / cropped.width
                target_height = int(target_width * aspect_ratio)
                
                cropped = cropped.resize((target_width, target_height), PILImage.Resampling.LANCZOS)
                
                return cropped
            
        except Exception as e:
            print(f"Error cropping card: {e}")
            return None

    def save_cropped_card(self, cropped_image: PILImage.Image, card_info=None):
        """Save the cropped card image to disk with timestamp and card info.
        
        Args:
            cropped_image: PIL Image of the cropped card
            card_info: Optional card information from recognition
            
        Returns:
            str: Path to saved file
        """
        try:
            # Create timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create filename based on card info if available
            if card_info and 'name' in card_info:
                # Clean up card name for filename (remove invalid characters)
                card_name = str(card_info['name']).replace('/', '_').replace('\\', '_').replace(':', '_')
                card_name = ''.join(c for c in card_name if c.isalnum() or c in (' ', '-', '_')).strip()
                filename = f"{timestamp}_{card_name}.png"
            else:
                filename = f"{timestamp}_unknown_card.png"
            
            # Full path
            filepath = os.path.join(self.save_directory, filename)
            
            # Save the image as PNG (lossless compression)
            cropped_image.save(filepath, "PNG", optimize=True)
            
            print(f"Cropped card image saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saving cropped card image: {e}")
            return None

    def draw_card_bounds(self, pil_image: PILImage.Image) -> PILImage.Image:
        """Draw a rectangle around a detected card in the image.
        
        Args:
            pil_image: PIL Image to process
            
        Returns:
            PIL Image with rectangle drawn around detected card
        """
        # Convert PIL to OpenCV format for drawing
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Detect card contour
        contour, bounding_rect = self.detect_card_contour(pil_image)
        
        if contour is not None:
            # Store for cropping
            self.last_card_contour = contour
            
            # Draw green rectangle around the detected card
            x, y, w, h = bounding_rect
            cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # Draw contour outline in yellow
            cv2.drawContours(cv_image, [contour], -1, (0, 255, 255), 2)
            
            # If we can approximate to 4 corners, draw corner points
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:
                # Draw corner points in red
                for point in approx:
                    cv2.circle(cv_image, tuple(point[0]), 8, (0, 0, 255), -1)
        else:
            self.last_card_contour = None

        # Convert back to PIL Image
        return PILImage.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

    def update_picam_texture(self, dt):
        if self.picam:
            # Capture frame from Pi camera
            frame = self.picam.capture_array()
            # Convert to format Kivy can display
            pil_img = PILImage.fromarray(frame)
            # Rotate the image 90 degrees
            pil_img = pil_img.rotate(90)
            # Mirror the image horizontally
            pil_img = PILImage.fromarray(cv2.flip(np.array(pil_img), 1))
            
            # Draw rectangle around detected card
            pil_img = self.draw_card_bounds(pil_img)
            
            # Convert to texture
            buf = pil_img.tobytes()
            texture = Texture.create(size=(pil_img.width, pil_img.height), colorfmt='rgb')
            texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            self.camera.texture = texture

    def update_preview(self, dt):
        """Update the card preview window"""
        try:
            if self.picam:
                # Capture from Pi camera
                frame = self.picam.capture_array()
                pil_img = PILImage.fromarray(frame)
                # Apply same transformations as main view
                pil_img = pil_img.rotate(90)
                pil_img = PILImage.fromarray(cv2.flip(np.array(pil_img), 1))
            else:
                # Capture from regular camera
                if not self.camera.texture:
                    return
                texture = self.camera.texture
                size = texture.size
                pixels = texture.pixels
                pil_img = PILImage.frombytes(mode="RGBA", size=size, data=pixels)
                
                # Draw rectangle around detected card for main camera view
                pil_img_with_bounds = self.draw_card_bounds(pil_img.convert('RGB'))
                
                # Update the camera view
                data = pil_img_with_bounds.tobytes()
                tex = Texture.create(size=pil_img_with_bounds.size, colorfmt='rgb')
                tex.blit_buffer(data, colorfmt='rgb', bufferfmt='ubyte')
                self.camera.texture = tex

            # Update card preview window
            if self.last_card_contour is not None:
                # Crop the card for preview
                cropped_card = self.crop_card_from_contour(pil_img.convert('RGB'), self.last_card_contour)
                
                if cropped_card:
                    # Convert cropped card to Kivy texture
                    cropped_card = cropped_card.convert("RGBA")
                    data = cropped_card.tobytes()
                    tex = Texture.create(size=cropped_card.size, colorfmt='rgba')
                    tex.blit_buffer(data, colorfmt='rgba', bufferfmt='ubyte')
                    self.card_preview.texture = tex
            else:
                # Clear preview if no card detected
                self.card_preview.texture = None
                
        except Exception as e:
            print(f"Error updating preview: {e}")

    def setup_camera(self):
        if PICAM_AVAILABLE:
            try:
                self.picam = Picamera2()
                config = self.picam.create_preview_configuration(
                        main={"size": (640, 480), "format": "RGB888"},
                        controls={"FrameDurationLimits": (33333, 33333)}  # ~30fps
                )
                self.picam.configure(config)
                self.picam.start()
                
                # Create a texture display widget
                self.camera = Image(size_hint=(1, 1))
                Clock.schedule_interval(self.update_picam_texture, 1.0/30.0)
            except Exception as e:
                print(f"Failed to initialize Pi camera: {e}")
                self.fallback_to_regular_camera()
        else:
            self.fallback_to_regular_camera()

    def fallback_to_regular_camera(self):
        self.picam = None
        self.camera = Camera(play=True, resolution=(640, 480), index=0)

    def submit_action(self, *args):
        """
        Capture camera frame and use CardScanner to detect the card.
        If a card contour was detected, use the cropped card for recognition and save it to disk.
        """
        try:
            if self.picam:
                # Capture from Pi camera
                frame = self.picam.capture_array()
                pil_img = PILImage.fromarray(frame)
                pil_img = pil_img.rotate(90)
                pil_img = PILImage.fromarray(cv2.flip(np.array(pil_img), 1))
            else:
                # Capture from regular camera
                if not self.camera.texture:
                    print("No camera texture available.")
                    return
                texture = self.camera.texture
                size = texture.size
                pixels = texture.pixels
                pil_img = PILImage.frombytes(mode="RGBA", size=size, data=pixels)

            # Use the cropped card if available, otherwise use full image
            image_to_scan = pil_img
            cropped_card = None
            
            if self.last_card_contour is not None:
                cropped_card = self.crop_card_from_contour(pil_img.convert('RGB'), self.last_card_contour)
                if cropped_card:
                    image_to_scan = cropped_card

            # Initialize scanner
            scanner = CardScanner()

            # Detect card
            card_info, confidence = scanner.detect_card(image_to_scan)
            
            # Save the cropped card image if we have one
            if cropped_card:
                saved_path = self.save_cropped_card(cropped_card, card_info)
                if saved_path:
                    print(f"Card image saved successfully to {saved_path}")
                else:
                    print("Failed to save card image")
            else:
                print("No cropped card available to save")
        
            # Switch to result screen and display card info
            app = App.get_running_app()
            result_screen = app.root.get_screen('card_result')
            result_screen.display_card(card_info, confidence)
            self.manager.current = 'card_result'
        
        except Exception as e:
            print(f"Error in card detection: {e}")
            # Show error on current screen
            self.title_label.text = f"Error: {str(e)}"

    def go_back(self, *args):
        if self.picam:
            self.picam.stop()
        self.manager.current = "menu"

    def on_enter(self):
        """Called when screen is entered"""
        app = App.get_running_app()
        if app.selected_library:
            try:
                library = app.selected_library
                self.library_label.text = f"Library: {library.name}"
            except Exception as e:
                print(f"Error fetching library details: {e}")
                self.library_label.text = "Library: Error loading details"