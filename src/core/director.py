from core.registry import Registry
import random

class Director:
    def __init__(self, game):
        self.game = game
        self.enemy_costs = {}
        self._load_costs()
    
    def _load_costs(self):
        """Loads enemy costs from Registry"""
        for enemy_type in Registry.get_enemy_types():
            config = Registry.get_enemy_config(enemy_type)
            if config:
                self.enemy_costs[enemy_type] = config.get("cost", 10)
    
    def calculate_difficulty_budget(self):
        """
        Formula: (CurrentFloor * 25) + (PlayerLevel * 15) + (TimePlayed / 10s)
        """

        
        # Floor factor
        floor_budget = self.game.current_layer_index * 25
        
        # Level factor
        player_budget = self.game.player.level * 15
        
        # Time factor (TimePlayed in ms)
        time_budget = (self.game.current_time / 10000) * 5 # Scaled down a bit from request?
        # Request said TimePlayed / 10s. If time is in ms: (ms / 1000) / 10 = ms / 10000.
        # But unit value? Let's assume +1 budget per 10s.
        time_budget = int(self.game.current_time / 10000)
        
        # Scaling if player is overpowered (optional/future)
        
        total = floor_budget + player_budget + time_budget
        return max(100, int(total)) # Minimum budget 100

    def generate_wave(self, budget, forbidden_types=None):
        """
        Buys enemies until budget runs out.
        """
        if forbidden_types is None:
            forbidden_types = ["JoernBoss"]
            
        wave = []
        remaining_budget = budget
        
        available_types = [
            etype for etype in self.enemy_costs.keys() 
            if etype not in forbidden_types
        ]
        
        if not available_types:
            return []
            
        attempts = 0
        while remaining_budget > 0 and attempts < 20:
            # Filter options affordable
            affordable = [t for t in available_types if self.enemy_costs[t] <= remaining_budget]
            
            if not affordable:
                break
                
            # Pick one
            choice = random.choice(affordable)
            cost = self.enemy_costs[choice]
            
            wave.append(choice)
            remaining_budget -= cost
            
            # Chance to stop if budget is low but not zero?
            # Or just greedily fill.
            
            attempts += 1 # Safety break
            
        return wave
