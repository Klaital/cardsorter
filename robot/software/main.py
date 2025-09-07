from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.camera import Camera


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

class CatalogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Camera widget
        self.camera = Camera(play=True)   # play=True starts the camera
        self.camera.resolution = (640, 480)
        layout.add_widget(self.camera)

        # Submit button
        submit_btn = Button(text="Submit", size_hint=(1, 0.2))
        submit_btn.bind(on_press=self.submit_action)
        layout.add_widget(submit_btn)

        # Back button
        back_btn = Button(text="Back", size_hint=(1, 0.2))
        back_btn.bind(on_press=self.menu)
        layout.add_widget(back_btn)

        self.add_widget(layout)
    def menu(self, *args):
        self.manager.current = "menu"

    def submit_action(self, instance):
        # Example: Capture the current camera frame
        filename = "captured.png"
        self.camera.export_to_png(filename)
        print(f"Saved image to {filename}")


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
