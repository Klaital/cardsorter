from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class Card:
    id: int
    library_id: int
    name: str
    set_name: str
    condition: str
    foil: bool
    collector_number: str
    usd_price: float
    created_at: datetime
    updated_at: datetime

@dataclass
class Library:
    id: int
    user_id: int
    name: str
    created_at: datetime
    updated_at: datetime

@dataclass
class CreateCardRequest:
    name: str
    set_name: str
    condition: str
    foil: bool = False
    collector_number: str = ""
    usd_price: float = 0.0

@dataclass
class CreateLibraryRequest:
    name: str
