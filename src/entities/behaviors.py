import pygame
from core.debug import debug
from config.settings import CELL_SIZE

class EnemyBehaviors:
    
    @staticmethod
    def melee_chase(enemy, flow_field, entities=None):
        """
        Simple chase behavior using flow field.
        """
        return flow_field.get_vector(enemy.x, enemy.y)

    @staticmethod
    def ranged_attack(enemy, flow_field, entities=None):
        """
        Follows flow field until within range, then stops to 'attack'.
        Actual attacking logic (projectiles) would be in enemy update/combat, 
        this just controls movement.
        """
        # Distance calculation
        dist_tiles = flow_field.get_distance(enemy.x, enemy.y)
        
        # Range check: e.g., 5 tiles. 
        # Using a fixed range or enemy attribute if available.
        # Ideally, we should use enemy.attack_range if added to config/class.
        start_attack_range = getattr(enemy, 'attack_range', 5)
        
        if dist_tiles > start_attack_range:
             return flow_field.get_vector(enemy.x, enemy.y)
        else:
             # Stop and allow shooting
             return (0, 0)

    @staticmethod
    def healer(enemy, flow_field, entities=None):
        """
        Healer Logic:
        1. Find injured allies (enemies with health < max_health).
        2. Move towards the closest one.
        3. If no injured allies, maybe follow player (flow field) or idle?
        """
        if entities is None: 
            return (0, 0)
            
        injured_allies = [
            e for e in entities 
            if e != enemy and hasattr(e, 'health') and e.health < e.max_health
        ]
        
        if not injured_allies:
            # Fallback: keep distance from player/flow field or idle
            # Let's just follow flow field but slowly? or idle.
            # "Move towards injured allies instead of the player."
            # If no injured allies, maybe we wander or stay put.
            return (0, 0)
            
        # Find closest injured ally
        closest_ally = None
        min_dist_sq = float('inf')
        
        for ally in injured_allies:
            dx = ally.x - enemy.x
            dy = ally.y - enemy.y
            d_sq = dx*dx + dy*dy
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                closest_ally = ally
                
        if closest_ally:
            # Move towards ally
            # Simple vector subtraction
            target_vec = pygame.math.Vector2(closest_ally.x - enemy.x, closest_ally.y - enemy.y)
            if target_vec.length() > 0:
                target_vec = target_vec.normalize()
                return (target_vec.x, target_vec.y)
        
        return (0, 0)

    @staticmethod
    def basic(enemy, flow_field, entities=None):
        return EnemyBehaviors.melee_chase(enemy, flow_field, entities)

    # Dictionary mapping behavior names to functions
    STRATEGIES = {
        "melee": melee_chase,
        "ranged": ranged_attack,
        "healer": healer,
        "basic": basic
    }

    @staticmethod
    def get_behavior(name):
        return EnemyBehaviors.STRATEGIES.get(name, EnemyBehaviors.basic)
