from datetime import datetime
from typing import Dict, List

import dateutil.parser

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
        self.set_code: str = kwargs.get("set_code", "")
        self.collector_number: str = kwargs.get("collector_number", "")
        self.name: str = kwargs.get("name", "")
        self.image_uris: Dict[str, str] = kwargs.get("image_uris", {})

def cards_from_json_array(json_array) -> List[Card]:
    """
    Deserialize an array of Card objects from a JSON array.

    Args:
        json_array (list): List of dictionaries containing card objects

    Returns:
        list[Card]: List of deserialized Card objects
    """
    return [Card(**item) for item in json_array]

