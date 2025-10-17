from datetime import datetime
from typing import Dict, List
import cv2
import os

import dateutil.parser
from kivy.app import App


class BulkDataDescription:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "")
        self.object = kwargs.get("object", "")
        self.type = kwargs.get("type", "")
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.download_uri = kwargs.get("download_uri", "")
        self._updated_at = kwargs.get("updated_at", "")
        self.size = kwargs.get("size", "")
        self.content_type = kwargs.get("content_type", "")
        self.content_encoding = kwargs.get("content_encoding", "")

    @property
    def updated_at(self) -> str:
        """Get the raw ISO 8601 timestamp string."""
        return self._updated_at

    @property
    def updated_at_datetime(self) -> datetime:
        """Get the updated_at value as a datetime object."""
        return dateutil.parser.isoparse(self._updated_at) if self._updated_at else datetime.min

    @classmethod
    def from_json_array(cls, json_array):
        """
        Deserialize an array of BulkDataDescription objects from a JSON array.
        
        Args:
            json_array (list): List of dictionaries containing bulk data descriptions
            
        Returns:
            list[BulkDataDescription]: List of deserialized BulkDataDescription objects
        """
        return [cls(**item) for item in json_array]

class Card:
    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", "")
        self.set_code: str = kwargs.get("set", "")
        self.collector_number: str = kwargs.get("collector_number", "")
        self.name: str = kwargs.get("name", "")
        self.image_uris: Dict[str, str] = kwargs.get("image_uris", {})
        self.faces: List[Face] = kwargs.get("card_faces", [])

        # Initialize a default Face if none are given. That means it's a single-faced card.
        if not self.faces:
            self.faces = [Face(id=self.id, name=self.name, image_uris=self.image_uris)]

    def setwithid(self) -> str:
        return f"{self.set_code}-{self.collector_number}"

class Face:
    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", "")
        self.card_id: str = kwargs.get("card_id", "")
        self.image_uris: Dict[str, str] = kwargs.get("image_uris", {})
        self.name: str = kwargs.get("name", "")
        self.local_image_path: str = kwargs.get("local_image_path", "")
        self.image_hash: str = kwargs.get("image_hash", "")

    @property
    def face_name(self):
        """Return the type of face this is. Expect mainly 'front' or 'back'."""
        uri = self.image_uris.get("normal")
        if uri:
            return uri.split("/")[4]
        else:
            return self.name

    def compute_local_image_path(self, root_dir: str):
        return os.path.join(root_dir, f"{self.id}.{self.face_name}.png")

    def compute_image_hash(self):
        """Load the image from disk and calculate a hash."""
        img = cv2.imread(self.local_image_path)
        if img is None:
            raise Exception(f"Could not load image {self.local_image_path}")
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Calculate the hash
        hasher = cv2.img_hash.PHash.create()
        return hasher.compute(gray)
    def compare_image_hash(self, other_hash):
        """Compare the hash of this face to a photograph of a card."""
        return cv2.img_hash.compare(self.image_hash, other_hash)

def cards_from_json_array(json_array) -> List[Card]:
    """
    Deserialize an array of Card objects from a JSON array.

    Args:
        json_array (list): List of dictionaries containing card objects

    Returns:
        list[Card]: List of deserialized Card objects
    """
    cards = [Card(**item) for item in json_array]
    for card in cards:
        # Ensure all card faces are tagged with the card ID
        for face in card.faces:
            face.card_id = card.id

    return cards

