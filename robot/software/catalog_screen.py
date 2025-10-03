import json

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
        right_panel = BoxLayout(orientation='vertical', size_hint=(0.6, 1))
        
        # Initialize camera
        self.picam = None
        self.setup_camera()
        
        # Camera view
        camera_container = BoxLayout(size_hint=(1, 0.8))
        camera_container.add_widget(self.camera)
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

    def draw_card_bounds(self, pil_image: PILImage.Image) -> PILImage.Image:
        """Draw a rectangle around a detected card in the image.
        
        Args:
            pil_image: PIL Image to process
            
        Returns:
            PIL Image with rectangle drawn around detected card
        """
        # Convert PIL to OpenCV format for contour detection
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale if needed
        if len(cv_image.shape) == 3:
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv_image

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

        if contours:
            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Check if contour is large enough (at least 10% of image area)
            image_area = gray.shape[0] * gray.shape[1]
            contour_area = cv2.contourArea(largest_contour)
            
            if contour_area > (image_area * 0.1):
                # Approximate the contour to a polygon
                epsilon = 0.02 * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)

                # If we have 4 points (rectangle)
                if len(approx) == 4:
                    # Draw green rectangle
                    cv2.drawContours(cv_image, [approx], -1, (0, 255, 0), 3)

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
        """Update the cropped preview"""
        try:
            if self.picam:
                # Capture from Pi camera
                frame = self.picam.capture_array()
                pil_img = PILImage.fromarray(frame)
            else:
                # Capture from regular camera
                if not self.camera.texture:
                    return
                texture = self.camera.texture
                size = texture.size
                pixels = texture.pixels
                pil_img = PILImage.frombytes(mode="RGBA", size=size, data=pixels)
                
                # Draw rectangle around detected card
                pil_img = self.draw_card_bounds(pil_img)
                
                # Update the camera view
                data = pil_img.tobytes()
                tex = Texture.create(size=pil_img.size)
                tex.blit_buffer(data, colorfmt='rgba', bufferfmt='ubyte')
                self.camera.texture = tex

            # Crop the image for preview
            W, H = pil_img.size
            top = int(0.9 * H)
            bottom = H
            left = int(W / 3)
            right = int(2 * W / 3)

            cropped = pil_img.crop((left, top, right, bottom))
            
            # Convert cropped PIL -> Kivy texture
            cropped = cropped.convert("RGBA")
            data = cropped.tobytes()
            tex = Texture.create(size=cropped.size)
            tex.blit_buffer(data, colorfmt="rgba", bufferfmt="ubyte")
            
            # Update the preview
            self.cropped_preview.texture = tex
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
        Capture camera frame, crop bottom middle third,
        and use CardScanner to detect the card.
        """
        try:
            if self.picam:
                # Capture from Pi camera
                frame = self.picam.capture_array()
                pil_img = PILImage.fromarray(frame)
            else:
                # Capture from regular camera
                if not self.camera.texture:
                    print("No camera texture available.")
                    return
                texture = self.camera.texture
                size = texture.size
                pixels = texture.pixels
                pil_img = PILImage.frombytes(mode="RGBA", size=size, data=pixels)

            # Initialize scanner
            scanner = CardScanner()

            # Detect card
            card_info, confidence = scanner.detect_card(pil_img)
        
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