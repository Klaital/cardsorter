from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from dotenv import load_dotenv
import os
from menu_screen import MenuScreen
from sort_screen import SortScreen
from login_screen import LoginScreen
from library_select_screen import LibrarySelectScreen
from catalog_screen import CatalogScreen
from card_result_screen import CardResultScreen
from magic_client import MagicClient
from token_manager import TokenManager

class CardSorterApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auth_token = None
        self.selected_library = None
        
        # Load environment variables
        load_dotenv()
        
        # Get configuration with fallbacks
        host = os.getenv('CARDSORTER_BACKEND_HOST', 'localhost')
        try:
            port = int(os.getenv('CARDSORTER_BACKEND_PORT', '9090'))
        except ValueError:
            print("Invalid port in environment variables, using default 9090")
            port = 9090
            
        self.magic_client = MagicClient(host=host, port=port)
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
            sm.add_widget(CardResultScreen(name="card_result"))
            
            return sm
        except Exception as e:
            print(f"Error initializing app: {str(e)}")
            raise