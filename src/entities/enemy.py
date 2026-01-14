import pygame
from entities.base import GridObject
from core.debug import debug
from config.settings import (
    CELL_SIZE,
    ENEMY_SPEED,
    ENEMY_HEALTH,
    COLOR_ENEMY,
    ENEMY_DAMAGE,
)


from core.physics import check_collision

from entities.behaviors import EnemyBehaviors

class Enemy(GridObject):
    def __init__(self, game, x, y, enemy_type="basic_enemy"):
        from core.registry import Registry

        config = Registry.get_enemy_config(enemy_type)
        if not config:
            print(f"Warning: Enemy type '{enemy_type}' not found. Using defaults.")
            # Fallback defaults
            w, h = 1, 1
            color = COLOR_ENEMY
            speed = ENEMY_SPEED
            health = ENEMY_HEALTH
            damage = ENEMY_DAMAGE
            xp_value = 10
            texture = None
            behavior_name = "melee"
            self.heal_amount = 0
            self.heal_cooldown = 2000
        else:
            w = config.get("width", 1)
            h = config.get("height", 1)
            color = tuple(config.get("color", COLOR_ENEMY))
            speed = config.get("speed", ENEMY_SPEED)
            health = config.get("health", ENEMY_HEALTH)
            damage = config.get("damage", ENEMY_DAMAGE)
            xp_value = config.get("xp_value", 10)
            texture = config.get("texture")
            behavior_name = config.get("behavior", "melee")
            self.attack_range = config.get("attack_range", 5)
            self.heal_amount = config.get("heal_amount", 0)
            self.heal_cooldown = config.get("heal_cooldown", 2000)
            
        self.behavior_name = behavior_name

        super().__init__(x, y, w, h, color=color)
        self.game = game
        self.speed = speed
        self.health = health
        self.max_health = health
        self.damage = damage
        self.xp_value = xp_value
        self.texture = texture
        self.enemy_type = enemy_type
        
        self.behavior = EnemyBehaviors.get_behavior(behavior_name)
        self.heal_cooldown_timer = 0
        self.wander_target = None
        self.wander_target = None
        self.wander_timer = 0
        
        self.last_attack_time = 0
        self.attack_cooldown = 2000 # Default, or could be in config
        
        # Minion Logic
        self.next_summon_type = None
        self.minion_damage_dealt = 0
        self.minion_healing_received = 0
        self.summoner = None



        # AI Control
        self.ai_controlled = False
        self.current_ai_action = 0
        self.ai_move_vector = (0, 0)

        self.is_shielded = False


    def draw(self, screen):
        if self.texture:
            # Scale texture if needed (or assume it's pre-scaled/correct size)
            # For now, let's scale it to the entity size
            scaled_texture = pygame.transform.scale(
                self.texture, (int(self.w * CELL_SIZE), int(self.h * CELL_SIZE))
            )
            screen.blit(scaled_texture, (self.x, self.y))
        else:
            super().draw(screen)

        # Health bar settings
        bar_width = self.w * CELL_SIZE
        bar_height = 5
        bar_x = self.x
        bar_y = self.y - 10  # 10 pixels above the enemy

        # Draw background (red)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # Draw health (green)
        if self.health > 0:
            health_width = bar_width * (self.health / self.max_health)
            pygame.draw.rect(
                screen, (0, 255, 0), (bar_x, bar_y, health_width, bar_height)
            )

    def take_damage(self, amount):
        if self.is_shielded:
            self.game.damage_texts.spawn(self.x, self.y - 20, "BLOCKED", color=(200, 200, 255))
            return

        self.health -= amount

        # Spawn floating damage text
        self.game.damage_texts.spawn(self.x, self.y - 10, amount)

        if self.health <= 0:
            self.die()

    def die(self):
        debug.log("Enemy died!")

    def _load_phase_texture(self, config_key):
        from core.registry import Registry
        import os
        config = Registry.get_enemy_config(self.enemy_type)
        path = config.get(config_key)
        if path:
             try:
                 full_path = os.path.normpath(os.path.join("src/config", path))
                 self.texture = pygame.image.load(full_path).convert_alpha()
                 debug.log(f"Loaded {config_key} from {full_path}")
             except Exception as e:
                 # print(f"Failed to load {config_key}: {e}")
                 pass




    def set_ai_action(self, action):
        self.current_ai_action = action
        self.ai_move_vector = (0, 0)
        
        # 0: Idle
        if action == 1: # Up
            self.ai_move_vector = (0, -1)
        elif action == 2: # Down
            self.ai_move_vector = (0, 1)
        elif action == 3: # Left
            self.ai_move_vector = (-1, 0)
        elif action == 4: # Right
            self.ai_move_vector = (1, 0)
            
        # Minion Choice Logic
        if action == 8:
            self.next_summon_type = "tank_enemy"
            self.current_ai_action = 6 # Trigger Summon (Ability 1)
        elif action == 9:
            self.next_summon_type = "ranger"
            self.current_ai_action = 6
        elif action == 10:
            self.next_summon_type = "healer"
            self.current_ai_action = 6
            
        # 5: Attack, 6: Ability 1, 7: Ability 2 are handled in update()

    def update(self, target_pos_or_flow_field, entities=None):
        current_time = pygame.time.get_ticks()

        dx, dy = 0, 0
        
        if self.ai_controlled:
            dx = self.ai_move_vector[0] * self.speed
            dy = self.ai_move_vector[1] * self.speed
            
            # Attack (5)
            if self.current_ai_action == 5:
                # Basic projectile attack (Reuse Ranged Logic basically)
                if current_time - self.last_attack_time > self.attack_cooldown:
                     from entities.projectile import Projectile
                     
                     # Standard Shot
                     player = self.game.player
                     p_dx = player.x - self.x
                     p_dy = player.y - self.y
                     
                     self.game.projectiles.append(
                        Projectile(
                            self.x, self.y,
                            direction=(p_dx, p_dy),
                            speed=6,
                            damage=self.damage,
                            owner_type="enemy",
                            texture=None,
                            visual_type="ARROW",
                            color=(150, 50, 255),
                            owner=self
                        )
                     )
                     self.last_attack_time = current_time
                     debug.log(f"AI Enemy Attacked!")

            # Action 6: Ability 1
            elif self.current_ai_action == 6:
                phase = getattr(self, 'phase', 1)
                if not hasattr(self, 'ability_cooldowns'): self.ability_cooldowns = {}
                
                if phase == 1:
                     # Summon Minions
                     if self.ability_cooldowns.get('summon', 0) <= 0:
                        from entities.boss.mechanics import perform_summon
                        perform_summon(self, self.game)
                        self.ability_cooldowns['summon'] = 5000 
                        
                elif phase == 2:
                    # Dash
                     if current_time - self.ability_cooldowns.get('dash', 0) > 5000:
                         self.is_dashing = True
                         self.dash_timer = current_time
                         self.dash_target = (self.game.player.x, self.game.player.y)
                         self.ability_cooldowns['dash'] = current_time
                         
                elif phase == 3:
                     # Shield
                     if current_time - self.ability_cooldowns.get('shield', 0) > 10000:
                         self.is_shielded = True
                         self.shield_timer = current_time
                         self.ability_cooldowns['shield'] = current_time

            # Action 7: Ability 2
            elif self.current_ai_action == 7:
                 phase = getattr(self, 'phase', 1)
                 if not hasattr(self, 'ability_cooldowns'): self.ability_cooldowns = {}

                 if phase == 1:
                    # Gravity Smash
                    if self.ability_cooldowns.get('gravity', 0) <= 0:
                        from entities.boss.mechanics import perform_gravity_smash
                        perform_gravity_smash(self, self.game.player)
                        self.ability_cooldowns['gravity'] = 6000
                 
                 elif phase == 3:
                    # Bullet Hell (Final Phase Ultimate)
                    from entities.boss.mechanics import perform_bullet_hell
                    perform_bullet_hell(self, self.game)

        elif hasattr(target_pos_or_flow_field, 'get_vector'):
            # Behavior Logic
            # behavior func signature: (enemy, flow_field, entities)
            if not hasattr(self, 'behavior') or self.behavior is None:
                print(f"WARNING: Enemy {self} missing behavior. Restoring default.")
                from entities.behaviors import EnemyBehaviors
                self.behavior = EnemyBehaviors.get_behavior(getattr(self, 'behavior_name', 'melee'))
                
            direction_tuple = self.behavior(self, target_pos_or_flow_field, entities)
            dx = direction_tuple[0] * self.speed
            dy = direction_tuple[1] * self.speed
            
            # Run heal logic if applicable
            self._try_heal(entities)
        else:
            # Fallback to direct seeking (target_pos)
            target_pos = target_pos_or_flow_field
            target = pygame.math.Vector2(target_pos)
            cur = pygame.math.Vector2(self.x, self.y)
            
            if cur.distance_to(target) > 0:
                direction = (target - cur).normalize()
                dx = direction.x * self.speed
                dy = direction.y * self.speed
        
        # End of Movement Logic (AI or Standard)
            
        # Apply movement with collision
        bounds = (0, 0, self.game.world.width * CELL_SIZE, self.game.world.height * CELL_SIZE)
        
        # Try moving X
        new_x = self.x + dx
        if not check_collision(new_x, self.y, self.w, self.h, bounds, self.game.world):
            self.x = new_x
            
        # Try moving Y
        new_y = self.y + dy
        if not check_collision(self.x, new_y, self.w, self.h, bounds, self.game.world):
            self.y = new_y
            
        # Ranged Attack Logic
        if dx == 0 and dy == 0 and self.behavior_name == "ranged":
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack_time > self.attack_cooldown:
                # Shoot at player
                player = self.game.player
                
                # Simple distance check is sufficient
                dist_sq = (player.x - self.x)**2 + (player.y - self.y)**2
                if dist_sq < (self.attack_range * CELL_SIZE)**2:
                    # Attack!
                    from entities.projectile import Projectile
                    
                    dx = self.game.player.x - self.x
                    dy = self.game.player.y - self.y
                    # Center to center
                    # ... simple enough for now
                    
                    self.game.projectiles.append(
                        Projectile(
                            self.x, self.y,
                            direction=(dx, dy),
                            speed=6,
                            damage=self.damage,
                            owner_type="enemy",
                            texture=None,
                            visual_type="ARROW",
                            color=(150, 50, 255), # Purple enemy arrow
                            owner=self
                        )
                    )
                    self.last_attack_time = current_time
                    debug.log(f"{self.enemy_type} fired projectile!")

    def _try_heal(self, entities):
        current_time = pygame.time.get_ticks()
        if self.heal_amount > 0:
             if current_time - self.heal_cooldown_timer > self.heal_cooldown:
                if entities:
                    # Find closest injured ally in range
                    closest_ally = None
                    min_dist_sq = (3 * CELL_SIZE) ** 2 # Max heal range 3 tiles (slightly larger than movement range logic to ensure connection)
                    
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
                            # debug.log(f"Healer healed for {healed_amt}. Ally HP: {closest_ally.health}")
                            self.heal_cooldown_timer = current_time

    # Serialization
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["game"]
        if "behavior" in state:
            del state["behavior"]
        state["texture"] = (
            None  # We might need to store texture path/type if we want to restore it exact
        )
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.game = None
        self.texture = None

    def post_load(self):
        # Restore texture
        if hasattr(self, "enemy_type"):
            from core.registry import Registry

            config = Registry.get_enemy_config(self.enemy_type)
            if config:
                self.texture = config.get("texture")
                
        # Restore behavior
        from entities.behaviors import EnemyBehaviors
        # Use stored behavior name if present, otherwise default to "melee"
        b_name = getattr(self, "behavior_name", "melee")
        self.behavior = EnemyBehaviors.get_behavior(b_name)
