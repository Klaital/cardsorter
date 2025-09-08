import jwt
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class TokenManager:
    def __init__(self):
        self.config_dir = Path.home() / '.cardsorter'
        self.token_file = self.config_dir / 'auth.json'
        self.ensure_config_dir()

    def ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_token(self, token):
        """Save token and selected library to file"""
        data = {
            'token': token,
            'saved_at': datetime.now().isoformat()
        }
        with open(self.token_file, 'w') as f:
            json.dump(data, f)

    def load_token(self):
        """Load token from file if it exists and is valid"""
        try:
            if not self.token_file.exists():
                return None

            with open(self.token_file, 'r') as f:
                data = json.load(f)

            token = data.get('token')
            if not token:
                return None

            # Decode token without verification to check expiration
            # Note: This doesn't validate the signature, just checks the expiration
            decoded = jwt.decode(token, options={"verify_signature": False})

            # Check if token expires within 8 hours
            exp_timestamp = decoded.get('exp')
            if not exp_timestamp:
                return None

            exp_time = datetime.fromtimestamp(exp_timestamp)
            if exp_time - datetime.now() < timedelta(hours=8):
                return None

            return token

        except (json.JSONDecodeError, jwt.InvalidTokenError, OSError) as e:
            print(f"Error loading token: {e}")
            return None

    def clear_token(self):
        """Remove saved token"""
        if self.token_file.exists():
            self.token_file.unlink()
