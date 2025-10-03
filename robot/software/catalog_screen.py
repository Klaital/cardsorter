import json
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
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Add library name label at the top
        self.library_label = Label(
            text="Library: None selected",
            font_size=20,
            size_hint=(1, 0.1),
            halign='left'
        )
        self.library_label.bind(size=self.library_label.setter('text_size'))
        self.layout.add_widget(self.library_label)
        
        # Initialize camera
        self.picam = None
        self.setup_camera()
        
        # Create a BoxLayout for camera and preview side by side
        camera_row = BoxLayout(orientation='horizontal', size_hint=(1, 0.5))
        
        # Camera view (left side)
        camera_container = BoxLayout(size_hint=(0.7, 1))
        camera_container.add_widget(self.camera)
        camera_row.add_widget(camera_container)
        
        # Preview (right side)
        preview_container = BoxLayout(size_hint=(0.3, 1))
        self.cropped_preview = Image(size_hint=(1, 1))
        preview_container.add_widget(self.cropped_preview)
        camera_row.add_widget(preview_container)
        
        self.layout.add_widget(camera_row)

        # Labels for card info
        self.title_label = Label(text="Title: ", font_size=18)
        self.set_label = Label(text="Set: ", font_size=18)
        self.num_label = Label(text="Collector Number: ", font_size=18)
        self.price_label = Label(text="Price: ", font_size=18)

        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.set_label)
        self.layout.add_widget(self.num_label)
        self.layout.add_widget(self.price_label)

        # Submit + Back buttons
        button_row = BoxLayout(size_hint=(1, 0.2), spacing=10)
        submit_btn = Button(text="Submit")
        submit_btn.bind(on_press=self.submit_action)
        button_row.add_widget(submit_btn)

        back_btn = Button(text="Back")
        back_btn.bind(on_press=self.go_back)
        button_row.add_widget(back_btn)

        self.layout.add_widget(button_row)
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

            # Crop the image
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
            
        self.layout.add_widget(self.camera)

    def fallback_to_regular_camera(self):
        self.picam = None
        self.camera = Camera(play=True, resolution=(640, 480), index=0)

    def update_picam_texture(self, dt):
        if self.picam:
            # Capture frame from Pi camera
            frame = self.picam.capture_array()
            # Convert to format Kivy can display
            pil_img = PILImage.fromarray(frame)
            buf = pil_img.tobytes()
            texture = Texture.create(size=(pil_img.width, pil_img.height), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera.texture = texture

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
            # TODO: remove this debug step
            pil_img = cv2.imread("scanner/testdata/spm0082_side1.jpg", cv2.IMREAD_UNCHANGED)
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