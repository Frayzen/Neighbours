import pygame
import random
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
    def __init__(self, game, x, y, enemy_type="basic_enemy", modifiers=None):
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
            animation_csv_path = config.get("animation_csv_path")
            
        self.behavior_name = behavior_name
        self.animation_csv_path = animation_csv_path
        
        # Apply Modifiers
        if modifiers:
            stat_mult = modifiers.get("stat_mult", 1.0)
            health = int(health * stat_mult)
            damage = int(damage * stat_mult)
            xp_value = int(xp_value * stat_mult)
            
            if "color_tint" in modifiers:
                tint = modifiers["color_tint"]
                color = (
                    max(0, color[0] - tint[0]),
                    max(0, color[1] - tint[1]),
                    max(0, color[2] - tint[2])
                )

        super().__init__(x, y, w, h, color=color)
        self.game = game
        self.speed = speed
        self.health = health
        self.max_health = health
        self.damage = damage
        self.base_damage = damage 
        self.xp_value = xp_value
        self.texture = texture
        self.enemy_type = enemy_type
        
        # Animation Setup
        from core.animation import AnimationController
        from config.animation_constants import ANIM_IDLE, ANIM_WALK
        import os
        from config.settings import BASE_DIR
        
        self.animator = AnimationController()
        self.use_animation = False
        
        if self.animation_csv_path:
             # Assume texture_path in config (which loaded self.texture) acts as the sheet?
             # Or we need the raw path. 
             # Registry loaded 'texture' but we might need the path to reload if needed?
             # Actually, AnimationController needs the Surface. self.texture is the Surface.
             # But 'load_from_csv' expects the surface.
             # 'load_from_paths' expects the path.
             
             # Let's try to use the raw path if we can find it, or use the loaded texture surface.
             # The registry config has 'texture_path'.
             texture_config_path = config.get("texture_path")
             if texture_config_path:
                 full_texture_path = os.path.normpath(os.path.join("src/config", texture_config_path))
                 full_csv_path = os.path.normpath(os.path.join("src/config", self.animation_csv_path))
                 
                 # Try loading
                 if self.animator.load_from_paths(full_csv_path, full_texture_path):
                     self.use_animation = True
                     self.animator.play(ANIM_IDLE)
                     debug.log(f"Enemy {enemy_type} animation loaded.")
        
        self.behavior = EnemyBehaviors.get_behavior(behavior_name)
        
        # Common cooldowns (subclasses can use them)
        self.attack_cooldown = 2000
        self.last_attack_time = 0
        self.next_attack_time = 0 

        # Wander stats
        self.wander_target = None
        self.wander_timer = 0
        
    def draw(self, screen):
        frame = self.animator.get_frame() if self.use_animation else None
        
        if frame:
            # Scale if needed
             target_w = int(self.w * CELL_SIZE)
             target_h = int(self.h * CELL_SIZE)
             if frame.get_width() != target_w or frame.get_height() != target_h:
                  frame = pygame.transform.scale(frame, (target_w, target_h))
             screen.blit(frame, (self.x, self.y))
             
        elif self.texture:
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
        bar_y = self.y - 10 

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
        self.game.damage_texts.spawn(self.x, self.y - 10, amount)

        if self.health <= 0:
            self.die()

    def die(self):
        debug.log(f"Enemy died: {self.enemy_type}")
        # Note: Proper removal from game list happens in Logic, 
        # but we mark it dead (health <= 0).

    def update(self, target_pos_or_flow_field, entities=None):
        # Base movement logic
        dx, dy = 0, 0
        
        if hasattr(target_pos_or_flow_field, 'get_vector'):
            if not hasattr(self, 'behavior') or self.behavior is None:
                 # Restore behavior if missing
                 self.behavior = EnemyBehaviors.get_behavior(getattr(self, 'behavior_name', 'melee'))
            
            direction_tuple = self.behavior(self, target_pos_or_flow_field, entities)
            dx = direction_tuple[0] * self.speed
            dy = direction_tuple[1] * self.speed
        else:
            # Fallback direct seeking
            target_pos = target_pos_or_flow_field
            target = pygame.math.Vector2(target_pos)
            cur = pygame.math.Vector2(self.x, self.y)
            if cur.distance_to(target) > 0:
                direction = (target - cur).normalize()
                dx = direction.x * self.speed
                dy = direction.y * self.speed
        
        # Update Animation State
        if self.use_animation:
             from config.animation_constants import ANIM_IDLE, ANIM_WALK
             if abs(dx) > 0.1 or abs(dy) > 0.1:
                 self.animator.play(ANIM_WALK)
             else:
                 self.animator.play(ANIM_IDLE)
             
             # Flip based on moving direction
             if dx < 0: self.animator.flip_x = True
             if dx > 0: self.animator.flip_x = False
             
             # Update animator (assume 60fps dt)
             dt = 1.0/60.0
             if hasattr(self.game, 'dt'): dt = self.game.dt
             self.animator.update(dt)

        return self._apply_movement(dx, dy)

    def _apply_movement(self, dx, dy):
        bounds = (0, 0, self.game.world.width * CELL_SIZE, self.game.world.height * CELL_SIZE)
        
        new_x = self.x + dx
        if not check_collision(new_x, self.y, self.w, self.h, bounds, self.game.world):
            self.x = new_x
            
        new_y = self.y + dy
        if not check_collision(self.x, new_y, self.w, self.h, bounds, self.game.world):
            self.y = new_y
            
    # Serialization
    def __getstate__(self):
        state = self.__dict__.copy()
        del state["game"]
        if "behavior" in state:
            del state["behavior"]
        state["texture"] = None 
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
        b_name = getattr(self, "behavior_name", "melee")
        self.behavior = EnemyBehaviors.get_behavior(b_name)
