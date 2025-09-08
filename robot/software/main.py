from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from catalog_screen import CatalogScreen
from login_screen import LoginScreen
from library_select_screen import LibrarySelectScreen
from magic_client.client import MagicClient

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
        self.manager.current = "login"


class CardSorterApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_token = None
        self.selected_library_id = None
        # Initialize with the correct base URL for your backend
        self.magic_client = MagicClient("http://localhost:8080")  # Adjust this URL to match your backend
        
    def build(self):
        try:
            print("Initializing Screens...")
            sm = ScreenManager()
            sm.add_widget(MenuScreen(name="menu"))
            sm.add_widget(SortScreen(name="sort"))
            sm.add_widget(LoginScreen(name="login"))
            sm.add_widget(LibrarySelectScreen(name="library_select"))
            sm.add_widget(CatalogScreen(name="catalog"))
            return sm
        except Exception as e:
            # This will help diagnose initialization errors
            print(f"Error initializing app: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        CardSorterApp().run()
    except Exception as e:
        print(f"Application crashed: {str(e)}")
        raise
