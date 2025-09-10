from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from menu_screen import MenuScreen
from sort_screen import SortScreen
from login_screen import LoginScreen
from library_select_screen import LibrarySelectScreen
from catalog_screen import CatalogScreen
from magic_client import MagicClient
from token_manager import TokenManager

class CardSorterApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_token = None
        self.selected_library = None
        self.magic_client: MagicClient = MagicClient("localhost", 9090)
        self.token_manager = TokenManager()
        
    def build(self):
        try:
            print("Initializing Screens...")
            # Request fullscreen mode
            from kivy.core.window import Window
            Window.fullscreen = 'auto'
            
            sm = ScreenManager()
            
            # Try to load a saved token
            saved_token = self.token_manager.load_token()
            if saved_token:
                self.auth_token = saved_token
                self.magic_client._auth_token = saved_token
                
            sm.add_widget(MenuScreen(name="menu"))
            sm.add_widget(SortScreen(name="sort"))
            sm.add_widget(LoginScreen(name="login"))
            sm.add_widget(LibrarySelectScreen(name="library_select"))
            sm.add_widget(CatalogScreen(name="catalog"))
            return sm
        except Exception as e:
            print(f"Error initializing app: {str(e)}")
            raise