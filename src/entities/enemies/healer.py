import pygame
import random
import math
from entities.enemies.enemy import Enemy
from core.debug import debug
from config.settings import CELL_SIZE

class Healer(Enemy):
    def __init__(self, game, x, y, enemy_type="basic_enemy", modifiers=None):
        super().__init__(game, x, y, enemy_type, modifiers)
        
        # Heal specific specific config fallback
        self.heal_amount = getattr(self, 'heal_amount', 0)
        
        from core.registry import Registry
        config = Registry.get_enemy_config(enemy_type)
        if config:
            self.heal_amount = config.get("heal_amount", 0)
            self.heal_cooldown = config.get("heal_cooldown", 2000)
        else:
             self.heal_cooldown = 2000

        self.heal_cooldown_timer = 0
        
        # Channeled Heal Stats
        self.channeled_heal_active = False
        self.channeled_heal_target = None
        self.channeled_heal_start_time = 0
        self.channeled_last_tick = 0
        self.channeled_check_timer = 0
        
        # Kamikaze Mode State
        self.kamikaze_mode = False

    def update(self, target_pos_or_flow_field, entities=None):
        # Kamikaze Logic
        if self.kamikaze_mode:
             # CHARGE PLAYER
             self.color = (255, 50, 0) # Turn Red
             self.damage = 0 # Disable contact damage so explosion hits clearly (no I-frames from bump)
             target_vec = pygame.math.Vector2(self.game.player.x - self.x, self.game.player.y - self.y)
             dist_to_player = target_vec.length()
             
             dx, dy = 0, 0
             if dist_to_player > 0:
                 target_vec = target_vec.normalize()
                 dx = target_vec.x * self.speed * 2.5 # Charge Speed (Very Fast!)
                 dy = target_vec.y * self.speed * 2.5
             
             # Check Collision with Player -> EXPLODE
             # Simple distance check for "touching"
             if dist_to_player < (self.w * CELL_SIZE * 0.8): # Touching
                 self._perform_self_destruct()
                 
             self._apply_movement(dx, dy)
             return

        # Restore Damage if we were in Kamikaze mode (and exited somehow - unlikely but safe)
        if self.damage == 0 and self.kamikaze_mode == False:
                self.damage = self.base_damage

        # Normal Behavior (mostly movement)
        super().update(target_pos_or_flow_field, entities)
        
        # Healer Logic
        if hasattr(target_pos_or_flow_field, 'get_vector'): # Only do complex logic if AI active
            self._try_heal(entities)
            self._handle_channeled_heal(entities)
            
            # Isolation/Kamikaze Check
            if self.heal_amount > 0 and self.enemy_type != "JoernBoss": 
                # Check for NON-HEALER allies in range 20
                has_combat_support = False
                isolation_range_sq = (20 * CELL_SIZE) ** 2
                
                if entities:
                    for entity in entities:
                        if entity is not self and isinstance(entity, Enemy) and entity.health > 0:
                            # Check Type/Behavior. We want "Protectors" (non-healers)
                            if getattr(entity, 'behavior_name', '') != "healer": 
                                dist_sq = (entity.x - self.x)**2 + (entity.y - self.y)**2
                                if dist_sq <= isolation_range_sq:
                                    has_combat_support = True
                                    break
                
                if not has_combat_support:
                        self.kamikaze_mode = True
                        debug.log(f"Healer {self} ISOLATED! ENTERING KAMIKAZE MODE!")

    def draw(self, screen):
        super().draw(screen)
        
        # Draw Channeled Heal Beam
        if self.channeled_heal_active and self.channeled_heal_target:
            target = self.channeled_heal_target
            start_pos = (self.x + self.w * CELL_SIZE // 2, self.y + self.h * CELL_SIZE // 2)
            end_pos = (target.x + target.w * CELL_SIZE // 2, target.y + target.h * CELL_SIZE // 2)
            
            # Animation: Pulse width
            time = pygame.time.get_ticks()
            width_pulse = max(1, int(math.sin(time * 0.01) * 2 + 3))
            
            # Draw Main Beam (Pink)
            pygame.draw.line(screen, (255, 105, 180), start_pos, end_pos, width_pulse)
            # Draw Core (Whiteish/lighter Pink)
            pygame.draw.line(screen, (255, 200, 220), start_pos, end_pos, 1)

        # Draw Kamikaze Firebolt Indicator
        if self.kamikaze_mode:
            # Draw a fireball "in hand" (offset to right/bottom)
            hand_offset_x = int(self.w * CELL_SIZE * 0.7)
            hand_offset_y = int(self.h * CELL_SIZE * 0.2)
            sh_x = self.x + hand_offset_x
            sh_y = self.y + hand_offset_y
            
            # Pulsing Fireball
            pulse = math.sin(pygame.time.get_ticks() * 0.02) * 3
            pygame.draw.circle(screen, (255, 69, 0), (sh_x, sh_y), 6 + pulse) # Red/Orange
            pygame.draw.circle(screen, (255, 255, 0), (sh_x, sh_y), 3) # Yellow core

    def die(self):
        self.channeled_heal_active = False # Clean up
        super().die()

    def _try_heal(self, entities):
        current_time = pygame.time.get_ticks()
        if self.heal_amount > 0:
             if current_time - self.heal_cooldown_timer > self.heal_cooldown:
                if entities:
                    # Find closest injured ally in range
                    closest_ally = None
                    min_dist_sq = (3 * CELL_SIZE) ** 2 # Max heal range 3 tiles
                    
                    found_target_dist = float('inf')

                    for ally in entities:
                        if ally == self or not isinstance(ally, Enemy):
                             continue
                        
                        if ally.health < ally.max_health:
                            dx = ally.x - self.x
                            dy = ally.y - self.y
                            d_sq = dx*dx + dy*dy
                            
                            # Prioritize closest
                            if d_sq <= min_dist_sq and d_sq < found_target_dist:
                                found_target_dist = d_sq
                                closest_ally = ally
                    
                    if closest_ally:
                        # Heal them
                        old_health = closest_ally.health
                        closest_ally.health = min(closest_ally.max_health, closest_ally.health + self.heal_amount)
                        healed_amt = closest_ally.health - old_health
                        
                        if healed_amt > 0:
                            self.game.damage_texts.spawn(
                                closest_ally.x, 
                                closest_ally.y - 20, 
                                healed_amt, 
                                color=(255, 105, 180), # Pink
                                prefix="+"
                            )
                            self.heal_cooldown_timer = current_time

    def _handle_channeled_heal(self, entities):
        current_time = pygame.time.get_ticks()
        
        # --- IF ACTIVE: MAINTAIN OR BREAK ---
        if self.channeled_heal_active:
            target = self.channeled_heal_target
            
            # Validation Checks
            if not target or target.health <= 0 or target.health >= target.max_health:
                self.channeled_heal_active = False
                self.channeled_heal_target = None
                return # Stop
            
            # Range Check (5 tiles = 5 * CELL_SIZE)
            dist_sq = (target.x - self.x)**2 + (target.y - self.y)**2
            if dist_sq > (5 * CELL_SIZE)**2:
                self.channeled_heal_active = False
                self.channeled_heal_target = None
                return # Stop (Out of range)
            
            # Apply Healing (1/sec)
            if current_time - self.channeled_last_tick > 1000:
                duration_sec = (current_time - self.channeled_heal_start_time) / 1000.0
                heal_amt = int(1 + duration_sec) # 1 + duration/sec
                
                old_health = target.health
                target.health = min(target.max_health, target.health + heal_amt)
                actual_heal = target.health - old_health
                
                if actual_heal > 0:
                     self.game.damage_texts.spawn(
                        target.x, target.y - 20, 
                        actual_heal, 
                        color=(255, 105, 180), # Pink
                        prefix="+"
                     )
                
                self.channeled_last_tick = current_time

        # --- IF INACTIVE: TRY TO START (5% CHECK) ---
        elif self.heal_amount > 0: # Only healers
            # Check periodically (every 1s) to avoid spam
            if current_time - self.channeled_check_timer > 1000:
                self.channeled_check_timer = current_time
                
                # 15% Chance
                if random.random() < 0.15:
                    # Find Target
                    best_target = None
                    min_dist_sq = (5 * CELL_SIZE) ** 2
                    
                    for ally in entities:
                        if ally == self or not isinstance(ally, Enemy): continue
                        if ally.health < ally.max_health:
                             d_sq = (ally.x - self.x)**2 + (ally.y - self.y)**2
                             if d_sq <= min_dist_sq:
                                 # Pick closest or just valid?
                                 # Let's pick this one
                                 best_target = ally
                                 break
                    
                    if best_target:
                        self.channeled_heal_active = True
                        self.channeled_heal_target = best_target
                        self.channeled_heal_start_time = current_time
                        self.channeled_last_tick = current_time

    def _perform_self_destruct(self):
        debug.log(f"Healer {self} SELF DESTRUCT!")
        
        # 1. Spawn Mega Fireball (Meteor)
        from entities.projectile import Projectile
        
        # Target SELF (Kamikaze throw on ground)
        target_x, target_y = self.x, self.y
        
        # Create Meteor
        self.game.projectiles.append(
            Projectile(
                self.x, self.y,
                direction=(0, 0), # No direction needed for target seeking or immediate drop
                speed=4, # Slower but big
                damage=100, # Massive damage
                owner_type="enemy",
                visual_type="METEOR",
                behavior="TARGET_EXPLOSION", # Explode at target
                target_pos=(target_x, target_y),
                color=(255, 50, 0),
                explode_radius=3 * CELL_SIZE
            )
        )
        
        # 2. Explode Self (Visuals + Death)
        self.game.damage_texts.spawn(self.x, self.y - 40, "SELF DESTRUCT", color=(255, 0, 0))
        self.health = 0
        self.die()
