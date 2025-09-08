from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.app import App

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Sort button
        sort_btn = Button(text="Sort", size_hint=(1, 0.2))
        sort_btn.bind(on_press=self.sort)
        layout.add_widget(sort_btn)

        # Catalog button
        catalog_btn = Button(text="Catalog", size_hint=(1, 0.2))
        catalog_btn.bind(on_press=self.catalog)
        layout.add_widget(catalog_btn)

        self.add_widget(layout)

    def sort(self, *args):
        self.manager.current = "sort"
    def catalog(self, *args):
        app = App.get_running_app()
        if app.auth_token:
            self.manager.current = "library_select"
        else:
            self.manager.current = "login"

