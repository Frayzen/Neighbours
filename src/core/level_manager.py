
import json
import os
from config.settings import BASE_DIR

class LevelManager:
    def __init__(self):
        self.levels = []
        self.current_level_index = 0
        self.load_layout()

    def load_layout(self):
        layout_path = os.path.join(BASE_DIR, "config", "level_layout.json")
        try:
            with open(layout_path, "r", encoding="utf-8") as f:
                raw_layout = json.load(f)
            
            # Parse and expand format
            self.levels = []
            for entry in raw_layout:
                if entry.get("type") == "dungeon":
                    # Expand count
                    count = entry.get("count", 1)
                    for i in range(count):
                        # Create individual level entries
                        new_entry = entry.copy()
                        del new_entry["count"]
                        new_entry["dungeon_index"] = i + 1
                        self.levels.append(new_entry)
                else:
                    self.levels.append(entry)
            
            print(f"LevelManager loaded {len(self.levels)} levels.")
            
        except Exception as e:
            print(f"Error loading level layout: {e}")
            # Fallback
            self.levels = [{ "type": "dungeon", "width": 64, "height": 64 }]

    def get_current_level(self):
        if 0 <= self.current_level_index < len(self.levels):
            return self.levels[self.current_level_index]
        return None

    def advance_level(self):
        if self.current_level_index < len(self.levels) - 1:
            self.current_level_index += 1
            return True
        return False
        
    def get_level_index(self):
        return self.current_level_index + 1
