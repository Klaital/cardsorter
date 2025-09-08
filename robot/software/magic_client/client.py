from typing import List, Optional
import requests
from datetime import datetime
from .models import Card, Library, CreateCardRequest, CreateLibraryRequest
from .exceptions import MagicClientError, AuthenticationError, NotFoundError, ValidationError

class MagicClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self._token = None

    def _handle_response(self, response: requests.Response):
        """Handle API response and raise appropriate exceptions"""
        if response.status_code == 401:
            raise AuthenticationError("Invalid credentials or token expired")
        elif response.status_code == 404:
            raise NotFoundError("Resource not found")
        elif response.status_code == 400:
            raise ValidationError(response.text)
        elif response.status_code >= 500:
            raise MagicClientError(f"Server error: {response.text}")

        return response

    def _get(self, path: str) -> dict:
        """Make GET request to API"""
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        response = self.session.get(f"{self.base_url}{path}", headers=headers)
        return self._handle_response(response).json()

    def _post(self, path: str, data: dict) -> dict:
        """Make POST request to API"""
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        response = self.session.post(f"{self.base_url}{path}", json=data, headers=headers)
        return self._handle_response(response).json()

    def _delete(self, path: str) -> None:
        """Make DELETE request to API"""
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        response = self.session.delete(f"{self.base_url}{path}", headers=headers)
        self._handle_response(response)

    def register(self, email: str, password: str) -> str:
        """Register a new user and return the authentication token"""
        data = {"email": email, "password": password}
        response = self._post("/register", data)
        self._token = response["token"]
        return self._token

    def login(self, email: str, password: str) -> str:
        """Login and return the authentication token"""
        data = {"email": email, "password": password}
        response = self._post("/login", data)
        self._token = response["token"]
        return self._token

    def create_library(self, name: str) -> int:
        """Create a new library and return its ID"""
        data = CreateLibraryRequest(name=name)
        response = self._post("/libraries", data.__dict__)
        return response["id"]

    def get_libraries(self) -> List[Library]:
        """Get all libraries for the authenticated user"""
        response = self._get("/libraries")
        if response is None:
            return []
        return [Library(**lib) for lib in response]

    def get_library(self, library_id: int) -> Library:
        """Get a specific library by ID"""
        response = self._get(f"/libraries/{library_id}")
        return Library(**response)

    def delete_library(self, library_id: int) -> None:
        """Delete a library by ID"""
        self._delete(f"/libraries/{library_id}")

    def create_card(self, library_id: int, card: CreateCardRequest) -> int:
        """Create a new card in the specified library and return its ID"""
        response = self._post(f"/libraries/{library_id}/cards", card.__dict__)
        return response["id"]

    def get_cards(self, library_id: int) -> List[Card]:
        """Get all cards in a library"""
        response = self._get(f"/libraries/{library_id}/cards")
        return [Card(**card) for card in response]

    def get_card(self, card_id: int) -> Card:
        """Get a specific card by ID"""
        response = self._get(f"/cards/{card_id}")
        return Card(**response)

    def move_card(self, card_id: int, new_library_id: int) -> None:
        """Move a card to a different library"""
        data = {"new_library_id": new_library_id}
        self._post(f"/cards/{card_id}/move", data)

    def delete_card(self, card_id: int) -> None:
        """Delete a card by ID"""
        self._delete(f"/cards/{card_id}")