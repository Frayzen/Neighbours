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
            texture = None
            behavior_name = "melee"
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
        self.health -= amount

        # Spawn floating damage text
        self.game.damage_texts.spawn(self.x, self.y - 10, amount)

        if self.health <= 0:
            self.die()

    def die(self):
        debug.log("Enemy died!")



    def update(self, target_pos_or_flow_field, entities=None):
        # Determine target direction
        dx, dy = 0, 0
        
        # Check if input is a FlowField (has get_vector method)
        if hasattr(target_pos_or_flow_field, 'get_vector'):
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
                    from entities.projectile import Projectile # Local import to avoid circular dependency if any
                    
                    # Direction
                    center_x = self.x + (self.w * CELL_SIZE)/2
                    center_y = self.y + (self.h * CELL_SIZE)/2
                    p_center_x = player.x + (player.w * CELL_SIZE)/2
                    p_center_y = player.y + (player.h * CELL_SIZE)/2
                    
                    direction = pygame.math.Vector2(p_center_x - center_x, p_center_y - center_y)
                    if direction.length() > 0:
                        direction = direction.normalize()
                        
                        proj = Projectile(
                            x=center_x, 
                            y=center_y, 
                            direction=direction, 
                            speed=8, # Fast enemy projectile
                            damage=self.damage, 
                            owner_type="enemy"
                        )
                        self.game.projectiles.append(proj)
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
