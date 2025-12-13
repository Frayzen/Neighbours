import json
import random
import os
from config.settings import BASE_DIR, RARITY_WEIGHTS
from items.item import Item

class ItemFactory:
    _items = []

    @staticmethod
    def load_items():
        items_path = os.path.join(BASE_DIR, "config", "items.json")
        try:
            with open(items_path, "r") as f:
                ItemFactory._items = json.load(f)
            print(f"Loaded {len(ItemFactory._items)} items.")
        except FileNotFoundError:
            print(f"Error: items.json not found at {items_path}")
            ItemFactory._items = []
        except json.JSONDecodeError:
            print(f"Error: items.json is not valid JSON.")
            ItemFactory._items = []

    @staticmethod
    def create_random_item(x, y, luck=1.0):
        if not ItemFactory._items:
            ItemFactory.load_items()
            if not ItemFactory._items:
                return None

        # Select rarity based on weights
        rarities = list(RARITY_WEIGHTS.keys())
        # Apply luck to rare and legendary weights
        weights = []
        for r in rarities:
            w = RARITY_WEIGHTS[r]
            if r in ["rare", "legendary"]:
                w *= luck
            weights.append(w)
            
        selected_rarity = random.choices(rarities, weights=weights, k=1)[0]

        # Filter items by rarity
        possible_items = [item for item in ItemFactory._items if item["rarity"] == selected_rarity]

        # If no items of selected rarity, fallback to any item
        if not possible_items:
            possible_items = ItemFactory._items

        # Select a random item
        item_data = random.choice(possible_items)
        
        return Item(x, y, item_data)
