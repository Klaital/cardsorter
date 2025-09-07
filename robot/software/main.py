from kivy.app import App
from catalog_screen import CatalogScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

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
        self.manager.current = "catalog"


class CardSorterApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(SortScreen(name="sort"))
        sm.add_widget(CatalogScreen(name="catalog"))
        return sm


if __name__ == "__main__":
    CardSorterApp().run()
