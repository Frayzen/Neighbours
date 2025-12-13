from entities.base import GridObject
from config.settings import COLOR_RARITY

class Item(GridObject):
    def __init__(self, x, y, item_data):
        super().__init__(x, y, 0.5, 0.5, color=COLOR_RARITY.get(item_data["rarity"], (255, 255, 255)))
        self.name = item_data["name"]
        self.type = item_data["type"]
        self.rarity = item_data["rarity"]
        self.effects = item_data["effects"]
        self.description = item_data["description"]
        self.target_weapon = item_data.get("target_weapon", None)
        self.target_tag = item_data.get("target_tag", None)
        self.duration = item_data.get("duration", 0)
