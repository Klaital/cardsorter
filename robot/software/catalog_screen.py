import json
import io
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from PIL import Image as PILImage


class CatalogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Camera feed
        self.camera = Camera(play=True, resolution=(640, 480), index=0)
        self.layout.add_widget(self.camera)

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

        # Load card database (still Scryfall format)
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

    def submit_action(self, *args):
        """
        Capture camera frame, crop bottom middle third,
        and display cropped image on screen.
        """
        if not self.camera.texture:
            print("No camera texture available.")
            return

        # Convert Kivy texture -> PIL Image
        texture = self.camera.texture
        size = texture.size
        pixels = texture.pixels  # raw RGBA bytes
        pil_img = PILImage.frombytes(mode="RGBA", size=size, data=pixels)

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

        # (Still placeholder detection until OCR is added)
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
        self.manager.current = "menu"
