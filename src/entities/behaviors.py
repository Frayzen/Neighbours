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
        - Wander randomly in the room.
        - The actual healing action is handled in Enemy.update's proximity check.
        """
        import random
        from config.settings import CELL_SIZE, SCREEN_WIDTH_PIX, SCREEN_HEIGHT_PIX
        
        current_time = pygame.time.get_ticks()
        
        # Check if we need a new target
        # - No target
        # - Reached target (rough check)
        # - Stuck/Time elapsed (optional)
        
        needs_target = False
        if not enemy.wander_target:
            needs_target = True
        else:
            tx, ty = enemy.wander_target
            dist_sq = (tx - enemy.x)**2 + (ty - enemy.y)**2
            if dist_sq < (CELL_SIZE/2)**2: # Reached within half a tile
                 needs_target = True
        
        # Periodic retargeting to avoid getting stuck or boring paths
        if current_time - enemy.wander_timer > 3000: # New target every 3s
            needs_target = True
            
        if needs_target:
            # Pick random point in valid room bounds
            # For simplicity, pick a point around current pos or totally random
            # Let's try totally random in world bounds? Or nearby?
            # Nearby is safer for not walking into walls continuously if walls are complex.
            # But "randomly in the room" implies exploring.
            
            # Simple approach: Random point within some radius (e.g., 5-10 tiles)
            radius = 200 # pixels
            
            valid = False
            for _ in range(5):
                angle = random.uniform(0, 6.28)
                dist = random.uniform(50, radius)
                
                off_x = dist * 1 # simplistic cos/sin replacement or just random xy
                off_x = random.randint(-radius, radius)
                off_y = random.randint(-radius, radius)
                
                tx = enemy.x + off_x
                ty = enemy.y + off_y
                
                # Bounds check
                if 0 <= tx < enemy.game.world.width * CELL_SIZE and 0 <= ty < enemy.game.world.height * CELL_SIZE:
                    # Walkability check
                    grid_x = int(tx / CELL_SIZE)
                    grid_y = int(ty / CELL_SIZE)
                    
                    cell = enemy.game.world.get_cell(grid_x, grid_y)
                    if cell and cell.walkable:
                            enemy.wander_target = (tx, ty)
                            enemy.wander_timer = current_time
                            valid = True
                            break
            
            if not valid:
                 # Just stand still or try again next frame
                 return (0, 0)
                 
        if enemy.wander_target:
            tx, ty = enemy.wander_target
            target_vec = pygame.math.Vector2(tx - enemy.x, ty - enemy.y)
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
