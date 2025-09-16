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

        # Enable keyboard auto popup
        Window.softinput_mode = 'below_target'

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Email input with keyboard focus
        self.email_input = TextInput(
            multiline=False,
            hint_text='Enter email',
            size_hint=(1, 0.2),
            use_bubble=True,  # Enable text bubble
            use_handles=True  # Enable selection handles
        )

        # Password input with keyboard focus
        self.password_input = TextInput(
            multiline=False,
            password=True,
            hint_text='Enter password',
            size_hint=(1, 0.2),
            use_bubble=True,  # Enable text bubble
            use_handles=True  # Enable selection handles
        )

        # Login button
        login_btn = Button(
            text="Login",
            size_hint=(1, 0.2)
        )
        login_btn.bind(on_press=self.login)

        # Back button
        back_btn = Button(
            text="Back",
            size_hint=(1, 0.2)
        )
        back_btn.bind(on_press=self.back_to_menu)

        # Error label (hidden by default)
        self.error_label = Label(
            text="",
            color=(1, 0, 0, 1),  # Red color
            size_hint=(1, 0.2)
        )

        # Add widgets to layout
        layout.add_widget(Label(text="Login", font_size=24))
        layout.add_widget(self.email_input)
        layout.add_widget(self.password_input)
        layout.add_widget(login_btn)
        layout.add_widget(back_btn)
        layout.add_widget(self.error_label)

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