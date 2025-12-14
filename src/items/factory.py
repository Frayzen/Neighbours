import json
import random
import os
import copy
from config.settings import BASE_DIR, RARITY_WEIGHTS, RARITY_SCALING
from items.item import Item

class ItemFactory:
    _items = []
    _sorted_items = {}
    
    @staticmethod
    def load_items():
        items_path = os.path.join(BASE_DIR, "config", "items.json")
        try:
            with open(items_path, "r") as f:
                raw_items_data = json.load(f)
            
            # Sort items into buckets for faster access
            ItemFactory._items = []
            ItemFactory._sorted_items = {
                "common": [],
                "rare": [],
                "legendary": []
            }
            
            for raw_item in raw_items_data:
                allowed_rarities = raw_item.get("allowed_rarities", [])
                
                # Legacy support or if no allowed_rarities defined
                if not allowed_rarities and "rarity" in raw_item:
                    allowed_rarities = [raw_item["rarity"]]
                
                for rarity in allowed_rarities:
                    # Create base copy
                    item_data = copy.deepcopy(raw_item)
                    item_data["rarity"] = rarity
                    
                    # Scale effects
                    multiplier = RARITY_SCALING.get(rarity, 1.0)
                    for effect_name, effect_data in item_data["effects"].items():
                         # Scaling only makes sense for numeric values (add/multiply)
                         # We don't scale "op" obviously.
                         if "value" in effect_data:
                             original_val = effect_data["value"]
                             # If it's a multiply op (e.g. 0.1 for 10%), we scale it directly?
                             # Or for "add" 10 -> 15.
                             if isinstance(original_val, (int, float)):
                                  # Round to 2 decimal places to avoid floating point mess
                                  item_data["effects"][effect_name]["value"] = round(original_val * multiplier, 2)
                    
                    # Add to main list and bucket
                    ItemFactory._items.append(item_data)
                    
                    if rarity in ItemFactory._sorted_items:
                        ItemFactory._sorted_items[rarity].append(item_data)
                    else:
                        pass # Should not happen if buckets are init correctly
            
            print(f"Loaded {len(ItemFactory._items)} items.")
        except FileNotFoundError:
            print(f"Error: items.json not found at {items_path}")
            ItemFactory._items = []
            ItemFactory._sorted_items = {}
        except json.JSONDecodeError:
            print(f"Error: items.json is not valid JSON.")
            ItemFactory._items = []
            ItemFactory._sorted_items = {}

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

        # Filter items by rarity using cached buckets
        possible_items = ItemFactory._sorted_items.get(selected_rarity, [])

        # If no items of selected rarity, fallback to any item
        if not possible_items:
            possible_items = ItemFactory._items

        # Select a random item
        item_data = random.choice(possible_items)
        
        return Item(x, y, item_data)
