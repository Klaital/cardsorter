from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.app import App
from kivy.core.window import Window

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.magic_client = App.get_running_app().magic_client

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Top section for inputs (1/3 of screen)
        top_section = BoxLayout(orientation='vertical', size_hint=(1, 0.33))
        
        # Title
        title_label = Label(
            text="Login",
            font_size=24,
            size_hint=(1, 0.2)
        )
        top_section.add_widget(title_label)

        # Email input
        self.email_input = TextInput(
            multiline=False,
            hint_text='Enter email',
            size_hint=(1, 0.4)
        )
        top_section.add_widget(self.email_input)

        # Password input
        self.password_input = TextInput(
            multiline=False,
            password=True,
            hint_text='Enter password',
            size_hint=(1, 0.4)
        )
        top_section.add_widget(self.password_input)

        # Add top section to main layout
        layout.add_widget(top_section)

        # Bottom section for buttons and error (2/3 of screen)
        bottom_section = BoxLayout(orientation='vertical', size_hint=(1, 0.67))

        # Error label
        self.error_label = Label(
            text="",
            color=(1, 0, 0, 1),  # Red color
            size_hint=(1, 0.2)
        )
        bottom_section.add_widget(self.error_label)

        # Buttons
        login_btn = Button(
            text="Login",
            size_hint=(1, 0.2)
        )
        login_btn.bind(on_press=self.login)

        back_btn = Button(
            text="Back",
            size_hint=(1, 0.2)
        )
        back_btn.bind(on_press=self.back_to_menu)

        bottom_section.add_widget(login_btn)
        bottom_section.add_widget(back_btn)

        # Add bottom section to main layout
        layout.add_widget(bottom_section)

        self.add_widget(layout)

    def login(self, *args):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        
        try:
            token = self.magic_client.login(email, password)
            app = App.get_running_app()
            app.auth_token = token
            app.token_manager.save_token(token)
            self.error_label.text = ""
            self.manager.current = "library_select"
        except Exception as e:
            self.error_label.text = f"Login failed: {str(e)}"

    def back_to_menu(self, *args):
        self.manager.current = "menu"