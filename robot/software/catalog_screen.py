import json
import io
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from PIL import Image as PILImage
from kivy.clock import Clock

# Try importing Picamera2 for Raspberry Pi camera support
try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAM_AVAILABLE = True
except ImportError:
    PICAM_AVAILABLE = False

class CatalogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Initialize camera
        self.picam = None
        self.setup_camera()
        
        # Cropped preview image placeholder
        self.cropped_preview = Image(size_hint=(1, 0.5))
        self.layout.add_widget(self.cropped_preview)

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

        # Load card database
        try:
            with open("cards.json", "r", encoding="utf-8") as f:
                self.cards = json.load(f)
        except FileNotFoundError:
            self.cards = []

        self.card_lookup = {}
        for card in self.cards:
            name = card.get("name")
            if name:
                self.card_lookup[name.lower()] = card

    def setup_camera(self):
        if PICAM_AVAILABLE:
            try:
                self.picam = Picamera2()
                config = self.picam.create_preview_configuration(
                    main={"size": (640, 480)},
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
            buf = frame.tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            self.camera.texture = texture

    def submit_action(self, *args):
        """
        Capture camera frame, crop bottom middle third,
        and display cropped image on screen.
        """
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

        self.cropped_preview.texture = tex

        # (Placeholder detection until OCR is added)
        detected_card = "Black Lotus"
        card_info = self.card_lookup.get(detected_card.lower())
        if card_info:
            self.title_label.text = f"Title: {card_info.get('name', 'Unknown')}"
            self.set_label.text = f"Set: {card_info.get('set_name', 'Unknown')}"
            self.num_label.text = f"Collector Number: {card_info.get('collector_number', 'N/A')}"
            price = card_info.get("prices", {}).get("usd") or "N/A"
            self.price_label.text = f"Price: ${price}"
        else:
            self.title_label.text = f"Card not found in database."
            self.set_label.text = ""
            self.num_label.text = ""
            self.price_label.text = ""

    def go_back(self, *args):
        if self.picam:
            self.picam.stop()
        self.manager.current = "menu"