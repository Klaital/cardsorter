import grpc
from . import user_pb2
from . import user_pb2_grpc
from . import library_pb2
from . import library_pb2_grpc
from . import cards_pb2
from . import cards_pb2_grpc


class MagicClient:
    def __init__(self, host="localhost", port=50051):
        """Initialize the Magic client.

        Args:
            host (str): The server host. Defaults to localhost.
            port (int): The server port. Defaults to 50051.
        """
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.user_stub = user_pb2_grpc.UserServiceStub(self.channel)
        self.library_stub = library_pb2_grpc.LibraryServiceStub(self.channel)
        self.cards_stub = cards_pb2_grpc.CardServiceStub(self.channel)
        self._auth_token = None

    def _get_auth_metadata(self):
        """Create metadata with authentication token."""
        return [('authorization', f'{self._auth_token}')] if self._auth_token else []

    def login(self, email: str, password: str) -> str:
        """Login with email and password.

        Args:
            email (str): User's email
            password (str): User's password

        Returns:
            str: Authentication token

        Raises:
            grpc.RpcError: If login fails
        """
        request = user_pb2.LoginRequest(email=email, password=password)
        response = self.user_stub.Login(request)
        self._auth_token = response.token
        return response.token

    def create_library(self, name: str) -> str:
        """Create a new card library.

        Args:
            name (str): Name of the library

        Returns:
            str: ID of the created library

        Raises:
            grpc.RpcError: If creation fails
        """
        metadata = self._get_auth_metadata()
        request = library_pb2.CreateLibraryRequest(name=name)
        response = self.library_stub.CreateLibrary(request, metadata=metadata)
        return response.library_id

    def get_libraries(self):
        """Get all libraries for the authenticated user.

        Returns:
            List of libraries

        Raises:
            grpc.RpcError: If request fails
        """
        metadata = self._get_auth_metadata()
        print(f"Refreshing library list from backend metadata={metadata}")
        request = library_pb2.GetLibrariesRequest()
        response = self.library_stub.GetLibraries(request, metadata=metadata)
        print(f"Got library response")
        return response.libraries

    def scan_card(self, image_bytes: bytes):
        """Scan a card from image data.

        Args:
            image_bytes (bytes): Raw image data of the card

        Returns:
            Card information

        Raises:
            grpc.RpcError: If scanning fails
        """
        metadata = self._get_auth_metadata()
        request = cards_pb2.ScanCardRequest(image=image_bytes)
        response = self.cards_stub.ScanCard(request, metadata=metadata)
        return response.card

    def add_card_to_library(self, library_id: str, card_id: str, quantity: int = 1):
        """Add a card to a library.

        Args:
            library_id (str): ID of the library
            card_id (str): ID of the card
            quantity (int): Number of copies to add. Defaults to 1.

        Raises:
            grpc.RpcError: If operation fails
        """
        metadata = self._get_auth_metadata()
        request = library_pb2.AddCardRequest(
            library_id=library_id,
            card_id=card_id,
            quantity=quantity
        )
        self.library_stub.AddCard(request, metadata=metadata)

    def remove_card_from_library(self, library_id: str, card_id: str, quantity: int = 1):
        """Remove a card from a library.

        Args:
            library_id (str): ID of the library
            card_id (str): ID of the card
            quantity (int): Number of copies to remove. Defaults to 1.

        Raises:
            grpc.RpcError: If operation fails
        """
        metadata = self._get_auth_metadata()
        request = library_pb2.RemoveCardRequest(
            library_id=library_id,
            card_id=card_id,
            quantity=quantity
        )
        self.library_stub.RemoveCard(request, metadata=metadata)

    def get_library_cards(self, library_id: str):
        """Get all cards in a library.

        Args:
            library_id (str): ID of the library

        Returns:
            List of cards with quantities

        Raises:
            grpc.RpcError: If request fails
        """
        metadata = self._get_auth_metadata()

        request = library_pb2.GetLibraryCardsRequest(library_id=library_id)
        response = self.library_stub.GetLibraryCards(request, metadata=metadata)
        return response.cards

    def close(self):
        """Close the gRPC channel."""
        self.channel.close()
