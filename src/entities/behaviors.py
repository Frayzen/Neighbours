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
    def boss_joern(enemy, flow_field, entities=None):
        """
        Full Boss Logic:
        - Phase 1: Melee chase + Gravity Smash
        - Phase 2: Daggers + Dash
        - Phase 3: Ranged Flee + Shield + Bullet Hell
        """
        import pygame
        from entities.boss.mechanics import (
            perform_gravity_smash, perform_summon, perform_dash, 
            activate_shield, perform_bullet_hell, perform_firebreath,
            perform_powerful_fireball,
            COOLDOWN_GRAVITY, COOLDOWN_SUMMON, COOLDOWN_DASH, 
            COOLDOWN_SHIELD, COOLDOWN_BULLET_HELL
        )
        
        current_time = pygame.time.get_ticks()
        player = enemy.game.player
        dist_to_player = ((player.x - enemy.x)**2 + (player.y - enemy.y)**2)**0.5
        
        # --- PHASE 1 (Hammer / Melee) ---
        if enemy.phase == 1:
            # Stats (Ensure Hammer stats)
            # Default is 5000 HP, slow speed.
            # "Lauf langsam auf Spieler zu" -> Default speed in config is 2.5, which is moderate.
            
            # Ability: Gravity Smash
            # "Wenn Cooldown bereit -> perform_gravity_smash"
            if "gravity" not in enemy.ability_cooldowns: enemy.ability_cooldowns["gravity"] = 0
            
            if current_time - enemy.ability_cooldowns["gravity"] > COOLDOWN_GRAVITY:
                perform_gravity_smash(enemy, player)
                enemy.ability_cooldowns["gravity"] = current_time
                # Also "Schlag" (Attack)? 
                # Enemy.update handles attacks if in range. Gravity smash pulls into range.
                
            # Ability: Summon (Bonus, not explicitly requested in Phase 4 prompt but was in Phase 3)
            if "summon" not in enemy.ability_cooldowns: enemy.ability_cooldowns["summon"] = 0
            if current_time - enemy.ability_cooldowns["summon"] > COOLDOWN_SUMMON:
                perform_summon(enemy, enemy.game)
                enemy.ability_cooldowns["summon"] = current_time

            # Movement: Chase
            return EnemyBehaviors.melee_chase(enemy, flow_field, entities)

        # --- PHASE 2 (Daggers / Dash) ---
        elif enemy.phase == 2:
            # Weapon Switch: Daggers
            # "Extrem schnell, geringer Schaden, sehr kurze Reichweite"
            # We enforce this by modifying enemy properties if not already set
            if getattr(enemy, 'current_weapon', '') != 'boss_daggers':
                enemy.current_weapon = 'boss_daggers'
                # Update stats manually to simulate weapon equip
                enemy.damage = 15
                enemy.attack_range = 1.5 # ~30 pixels approx
                # enemy.speed = 4 # Increase speed? Prompt says "Extrem schnell" for *weapon*. 
                # Usually weapon doesn't change move speed unless we say so. 
                # Dash ability handles bursts.
            
            # Ability: Dash
            # "Wenn Distanz > X -> perform_dash"
            if dist_to_player > 150: # X = 150
                if "dash" not in enemy.ability_cooldowns: enemy.ability_cooldowns["dash"] = 0
                if current_time - enemy.ability_cooldowns["dash"] > COOLDOWN_DASH:
                    perform_dash(enemy, player)
                    enemy.ability_cooldowns["dash"] = current_time
            
            # Ability: Firebreath (Mid-range / General aggression)
            # REMOVED from Phase 2 as per request

            # Movement: Chase (but faster? or just dash?)
            # Prompt says "Wechsle Waffe zu Dolchen"
            return EnemyBehaviors.melee_chase(enemy, flow_field, entities)

        # --- PHASE 3 (Staff / Ranged) ---
        elif enemy.phase == 3:
            # Weapon Switch: Staff
            if getattr(enemy, 'current_weapon', '') != 'boss_staff':
                 enemy.current_weapon = 'boss_staff'
                 enemy.damage = 90
                 enemy.attack_range = 10 
                 # Switch behavior to ranged? The update loop calls this behavior function.
                 # So we return ranged movement vector here.
            
            # Ability: Shield
            # "Wenn Spieler schießt -> activate_shield"
            # Check for incoming player projectiles
            incoming_threat = False
            for proj in enemy.game.projectiles:
                if proj.owner_type == "player":
                    # Check distance
                    p_dist = ((proj.x - enemy.x)**2 + (proj.y - enemy.y)**2)**0.5
                    if p_dist < 150: # React distance
                        incoming_threat = True
                        break
            
            if incoming_threat:
                if "shield" not in enemy.ability_cooldowns: enemy.ability_cooldowns["shield"] = 0
                if current_time - enemy.ability_cooldowns["shield"] > COOLDOWN_SHIELD:
                    activate_shield(enemy)
                    enemy.ability_cooldowns["shield"] = current_time

            # Ability: Firebreath (New Phase 3 Ability)
            # Use somewhat frequent cooldown
            if "firebreath" not in enemy.ability_cooldowns: enemy.ability_cooldowns["firebreath"] = 0
            if current_time - enemy.ability_cooldowns["firebreath"] > 7000: # 7 seconds
                perform_firebreath(enemy, enemy.game, player)
                enemy.ability_cooldowns["firebreath"] = current_time

            # Ability: Powerful Fireball (New Request)
            if "powerful_fireball" not in enemy.ability_cooldowns: enemy.ability_cooldowns["powerful_fireball"] = 0
            if current_time - enemy.ability_cooldowns["powerful_fireball"] > 8000: # 8 seconds
                perform_powerful_fireball(enemy, enemy.game, player)
                enemy.ability_cooldowns["powerful_fireball"] = current_time

            # Ability: Summon (Re-added to Phase 3)
            # Reuse Phase 1 Logic
            if "summon" not in enemy.ability_cooldowns: enemy.ability_cooldowns["summon"] = 0
            if current_time - enemy.ability_cooldowns["summon"] > 12000: # 12 seconds (less frequent than P1)
                perform_summon(enemy, enemy.game)
                enemy.ability_cooldowns["summon"] = current_time

            # Ability: Bullet Hell
            # "Alle 5 Sekunden -> perform_bullet_hell"
            if "bullet_hell" not in enemy.ability_cooldowns: enemy.ability_cooldowns["bullet_hell"] = 0
            if current_time - enemy.ability_cooldowns["bullet_hell"] > 5000: # 5 seconds
                perform_bullet_hell(enemy, enemy.game)
                enemy.ability_cooldowns["bullet_hell"] = current_time
            
            # Movement: Keep Distance / Flee
            # Use ranged behavior? Or custom flee logic
            # "Bleib auf Distanz (fliehe, wenn Spieler zu nah)"
            
            ideal_dist = 200
            if dist_to_player < ideal_dist:
                # Flee: Vector FROM player
                dx = enemy.x - player.x
                dy = enemy.y - player.y
                # Normalize
                if dist_to_player > 0:
                    return (dx/dist_to_player, dy/dist_to_player)
                else:
                    return (1, 0) # Panic move
            elif dist_to_player > ideal_dist + 50:
                 # Chase a bit to get in range
                 return EnemyBehaviors.melee_chase(enemy, flow_field, entities)
            else:
                 # Maintain
                 return (0, 0)
        
        # Fallback
        return EnemyBehaviors.melee_chase(enemy, flow_field, entities)

    @staticmethod
    def basic(enemy, flow_field, entities=None):
        return EnemyBehaviors.melee_chase(enemy, flow_field, entities)

    # Dictionary mapping behavior names to functions
    STRATEGIES = {
        "melee": melee_chase,
        "ranged": ranged_attack,
        "healer": healer,
        "boss_joern": boss_joern,
        "basic": basic
    }

    @staticmethod
    def get_behavior(name):
        return EnemyBehaviors.STRATEGIES.get(name, EnemyBehaviors.basic)
