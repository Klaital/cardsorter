
class Set:
    def __init__(self, scryfall_id, name, code, released_at, set_type, card_count):
        self.scryfall_id = scryfall_id
        self.name = name
        self.code = code
        self.released_at = released_at
        self.set_type = set_type
        self.card_count = card_count

def from_json_array(json_data) -> list[Set]:
    return [Set(**set_data) for set_data in json_data]

def sort_by_release_date(sets: list[Set]) -> list[Set]:
    return sorted(sets, key=lambda s: s.released_at, reverse=True)