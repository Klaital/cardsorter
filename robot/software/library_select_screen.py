from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.app import App

class CreateLibraryPopup(Popup):
    def __init__(self, on_create_callback, **kwargs):
        super().__init__(**kwargs)
        self.title = "Create New Library"
        self.size_hint = (0.8, 0.4)
        self.on_create_callback = on_create_callback

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.name_input = TextInput(
            multiline=False,
            hint_text='Library Name',
            size_hint=(1, 0.5)
        )

        buttons_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.5), spacing=10)

        create_btn = Button(text='Create')
        create_btn.bind(on_press=self.create_library)

        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=self.dismiss)

        buttons_layout.add_widget(create_btn)
        buttons_layout.add_widget(cancel_btn)

        layout.add_widget(self.name_input)
        layout.add_widget(buttons_layout)

        self.content = layout

    def create_library(self, *args):
        name = self.name_input.text.strip()
        if name:
            self.on_create_callback(name)
            self.dismiss()


class LibrarySelectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.libraries = []
        self.magic_client = App.get_running_app().magic_client

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Header
        self.layout.add_widget(Label(
            text="Select Library",
            font_size=24,
            size_hint=(1, 0.1)
        ))

        # Libraries container
        self.libraries_layout = GridLayout(
            cols=1,
            spacing=10,
            size_hint=(1, 0.7)
        )
        self.layout.add_widget(self.libraries_layout)

        # Buttons layout
        buttons_layout = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint=(1, 0.2)
        )

        create_btn = Button(text="Create Library")
        create_btn.bind(on_press=self.show_create_popup)

        back_btn = Button(text="Back")
        back_btn.bind(on_press=self.back_to_menu)

        buttons_layout.add_widget(create_btn)
        buttons_layout.add_widget(back_btn)
        self.layout.add_widget(buttons_layout)

        # Error label
        self.error_label = Label(
            text="",
            color=(1, 0, 0, 1),
            size_hint=(1, 0.1)
        )
        self.layout.add_widget(self.error_label)

        self.add_widget(self.layout)

    def on_enter(self):
        """Called when the screen is entered - refresh libraries list"""
        self.load_libraries()

    def load_libraries(self):
        """Load and display libraries from the backend"""
        try:
            self.libraries_layout.clear_widgets()
            self.libraries = self.magic_client.get_libraries()

            if not self.libraries:
                self.libraries_layout.add_widget(Label(
                    text="No libraries found. Create one to get started!",
                    size_hint=(1, None),
                    height=40
                ))
            else:
                for library in self.libraries:
                    btn = Button(
                        text=f"{library.name}",
                        size_hint=(1, None),
                        height=40
                    )
                    btn.library_id = library.id
                    btn.bind(on_press=self.select_library)
                    self.libraries_layout.add_widget(btn)

            self.error_label.text = ""

        except Exception as e: # TODO: narrow this down to the right type
            self.error_label.text = f"Error loading libraries: {str(e)}"

    def show_create_popup(self, *args):
        popup = CreateLibraryPopup(on_create_callback=self.create_library)
        popup.open()

    def create_library(self, name):
        try:
            library_id = self.magic_client.create_library(name)
            # Store the library ID in the app
            App.get_running_app().selected_library_id = library_id
            # Navigate to catalog screen
            self.manager.current = "catalog"
        except Exception as e: # TODO: narrow this down to the right type
            self.error_label.text = f"Error creating library: {str(e)}"

    def select_library(self, button):
        # Store the selected library ID in the app
        selected_library = None
        for l in self.libraries:
            if l.id == button.library_id:
                App.get_running_app().selected_library = l

        # Navigate to catalog screen
        self.manager.current = "catalog"

    def back_to_menu(self, *args):
        self.manager.current = "menu"