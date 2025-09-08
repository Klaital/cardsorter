from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.button import Button

class SortScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        layout.add_widget(Label(text="Coming soon", font_size=24))
        layout.add_widget(Button(
            text="Back", size_hint=(1, 0.2),
            on_press=self.menu
        ))
        self.add_widget(layout)
    def menu(self, *args):
        self.manager.current = "menu"
