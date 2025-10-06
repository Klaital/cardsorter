from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.app import App


class CardResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Title at the top
        self.title = Label(
            text="Card Detection Result",
            font_size=24,
            size_hint=(1, 0.1)
        )
        self.layout.add_widget(self.title)

        # Card info labels
        self.name_label = Label(text="Name: ", font_size=18)
        self.set_label = Label(text="Set: ", font_size=18)
        self.collector_label = Label(text="Collector Number: ", font_size=18)
        self.price_label = Label(text="Price: ", font_size=18)

        # Add labels to layout
        self.layout.add_widget(self.name_label)
        self.layout.add_widget(self.set_label)
        self.layout.add_widget(self.collector_label)
        self.layout.add_widget(self.price_label)

        # Buttons
        button_row = BoxLayout(size_hint=(1, 0.2), spacing=10)

        retry_btn = Button(text="Try Again")
        retry_btn.bind(on_press=self.try_again)
        button_row.add_widget(retry_btn)

        back_btn = Button(text="Back to Menu")
        back_btn.bind(on_press=self.back_to_menu)
        button_row.add_widget(back_btn)

        self.layout.add_widget(button_row)
        self.add_widget(self.layout)

        if 'card_info' in kwargs:
            self.display_card(kwargs['card_info'], kwargs['confidence'])

    def display_card(self, card_info, confidence):
        """Update the display with card information"""
        if card_info:
            self.name_label.text = f"Name: {card_info.get('name', 'Unknown')}"
            self.set_label.text = f"Set: {card_info.get('set_name', 'Unknown')}"
            self.collector_label.text = f"Collector Number: {card_info.get('collector_number', 'Unknown')}"
            price = card_info.get('prices', {}).get('usd', 'N/A')
            self.price_label.text = f"Price: ${price}"
            self.title.text = f"Card Detected! (Confidence: {confidence:.2f})"
        else:
            self.title.text = "No Card Detected"
            self.name_label.text = "Name: Not Found"
            self.set_label.text = "Set: Not Found"
            self.collector_label.text = "Collector Number: Not Found"
            self.price_label.text = "Price: Not Found"

    def try_again(self, *args):
        """Return to the catalog screen to try another scan"""
        self.manager.current = 'catalog'

    def back_to_menu(self, *args):
        """Return to the main menu"""
        self.manager.current = 'menu'