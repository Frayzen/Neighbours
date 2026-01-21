import pygame
import random
from entities.enemies.enemy import Enemy
from core.debug import debug
from config.settings import CELL_SIZE

class RangedEnemy(Enemy):
    def __init__(self, game, x, y, enemy_type="basic_enemy", modifiers=None):
        super().__init__(game, x, y, enemy_type, modifiers)
        
        # Ranged Stats
        from core.registry import Registry
        config = Registry.get_enemy_config(enemy_type)
        if config:
            self.attack_range = config.get("attack_range", 5)
        else:
            self.attack_range = 5
            
        # Rapid Fire Stats
        self.rapid_fire_active = False
        self.rapid_fire_shots_left = 0
        self.rapid_fire_last_shot_time = 0

    def update(self, target_pos_or_flow_field, entities=None):
        # Determine if we are stationary (moving logic handles movement)
        # Note: In original code, ranged logic ran *inside* update.
        # Here we run it alongside or after movement. 
        # If rapid firing, we should FREEZE movement.
        
        dx, dy = 0, 0
        
        if self.rapid_fire_active:
            # Freeze movement
            pass 
        else:
            # Normal movement via super
            super().update(target_pos_or_flow_field, entities)
            
        # Attack Logic (Always run, even if moving/frozen)
        current_time = pygame.time.get_ticks()

        # --- RAPID FIRE SEQUENCE ---
        if self.rapid_fire_active:
            # Fire next shot or end sequence
            if current_time - self.rapid_fire_last_shot_time > 150: # 150ms between rapid shots
                self._fire_projectile()
                self.rapid_fire_shots_left -= 1
                self.rapid_fire_last_shot_time = current_time
                
                if self.rapid_fire_shots_left <= 0:
                    self.rapid_fire_active = False
                    # Long cooldown after rapid fire
                    self.next_attack_time = current_time + self.attack_cooldown + random.randint(500, 1000)
                    debug.log(f"{self.enemy_type} finished Rapid Fire sequence.")

        # --- NORMAL ATTACK CHECK ---
        elif current_time > self.next_attack_time:
            # Check distance
            player = self.game.player
            dist_sq = (player.x - self.x)**2 + (player.y - self.y)**2
            
            # Only attack if in range
            if dist_sq < (self.attack_range * CELL_SIZE)**2:
                # Check line of sight? (Original didn't)
                
                # 20% Chance for Rapid Fire
                if random.random() < 0.20:
                    self.rapid_fire_active = True
                    self.rapid_fire_shots_left = 5
                    self.rapid_fire_last_shot_time = current_time
                    
                    self._fire_projectile()
                    self.rapid_fire_shots_left -= 1
                    
                    debug.log(f"{self.enemy_type} STARTING RAPID FIRE!")
                
                else:
                    # Normal Shot
                    self._fire_projectile()
                    
                    # Variable Cooldown
                    variance = random.randint(-400, 400)
                    self.next_attack_time = current_time + self.attack_cooldown + variance
                    self.last_attack_time = current_time

    def _fire_projectile(self):
        from entities.projectile import Projectile
        
        # Calculate direction to player
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        
        # Randomize Speed slightly
        speed = random.uniform(5.5, 8.5)
        
        self.game.projectiles.append(
            Projectile(
                self.x, self.y,
                direction=(dx, dy),
                speed=speed,
                damage=self.damage,
                owner_type="enemy",
                texture=None,
                visual_type="ARROW",
                color=(150, 50, 255) # Purple enemy arrow
            )
        )
