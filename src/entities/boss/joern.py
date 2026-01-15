import pygame
from entities.enemy import Enemy
from core.debug import debug
from config.settings import CELL_SIZE
from core.physics import check_collision
from core.vfx import vfx_manager, ExplosionEffect

class JoernBoss(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, enemy_type="JörnBoss")
        
        self.phase = 1
        self.ability_cooldowns = { 
            "summon": 0, 
            "dash": 0, 
            "shield": 0, 
            "gravity": 0,
            "bullet_hell": 0
        }
        self.is_shielded = False
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_target = (0, 0)
        self.shield_timer = 0
        
        self.ai_controlled = False 
        self.current_ai_action = 0
        self.ai_move_vector = (0, 0)
        
        debug.log("JoernBoss Initialized via class!")

    def take_damage(self, amount):
        if self.phase == 1:
            amount *= 0.65
            self.game.damage_texts.spawn(self.x, self.y - 25, "RESIST", color=(100, 100, 255))
        elif self.phase == 3:
            amount *= 1.20
            self.game.damage_texts.spawn(self.x, self.y - 25, "WEAK!", color=(255, 50, 50))

        super().take_damage(amount)

    def update(self, target_pos_or_flow_field, entities=None):
        current_time = pygame.time.get_ticks()

        # --- Phase Management ---
        hp_percent = self.health / self.max_health
        
        if hp_percent < 0.66 and self.phase < 2:
            self.phase = 2
            self.color = (255, 100, 0) 
            debug.log(f"{self.enemy_type} entered Phase 2!")
            vfx_manager.add_effect(ExplosionEffect(self.x, self.y, radius=100, color=(255, 165, 0)))
            self._load_phase_texture("texture_phase_2")
            
        if hp_percent < 0.33 and self.phase < 3:
            self.phase = 3
            self.color = (255, 0, 0) 
            debug.log(f"{self.enemy_type} entered Phase 3!")
            from entities.boss.mechanics import perform_The_Final_Ember
            perform_The_Final_Ember(self, self.game)
            vfx_manager.add_effect(ExplosionEffect(self.x, self.y, radius=150, color=(255, 0, 0)))
            self._load_phase_texture("texture_phase_3")

        # --- Mechanics Durations ---
        from entities.boss.mechanics import SHIELD_DURATION, DASH_DURATION, DASH_SPEED_MULTIPLIER

        if self.is_shielded:
            if current_time - self.shield_timer > SHIELD_DURATION:
                self.is_shielded = False
                from core.registry import Registry
                self.color = Registry.get_enemy_config(self.enemy_type).get("color", (255,0,0))
                if self.phase == 2: self.color = (255, 100, 0)
                if self.phase == 3: self.color = (255, 0, 0)

        if self.is_dashing:
             if current_time - self.dash_timer > DASH_DURATION:
                 self.is_dashing = False

        # --- Movement Logic ---
        if self.is_dashing:
             tx, ty = self.dash_target
             dx = tx - self.x
             dy = ty - self.y
             dist = (dx**2 + dy**2)**0.5
             move_speed = self.speed * DASH_SPEED_MULTIPLIER
             
             if dist < move_speed:
                 self.x = tx; self.y = ty; self.is_dashing = False
             else:
                 self.x += (dx/dist) * move_speed
                 self.y += (dy/dist) * move_speed
             
             player_rect = pygame.Rect(self.game.player.x, self.game.player.y, self.game.player.w * CELL_SIZE, self.game.player.h * CELL_SIZE)
             my_rect = pygame.Rect(self.x, self.y, self.w * CELL_SIZE, self.h * CELL_SIZE)
             if my_rect.colliderect(player_rect):
                 self.game.player.take_damage(25)
             return 

        # 2. Standard Movement
        dx, dy = 0, 0
        
        if self.ai_controlled:
            dx = self.ai_move_vector[0] * self.speed
            dy = self.ai_move_vector[1] * self.speed
            
            # Action 5: Attack
            if self.current_ai_action == 5:
                if current_time - self.last_attack_time > self.attack_cooldown:
                     from entities.projectile import Projectile
                     if self.phase == 3:
                         from entities.boss.mechanics import perform_powerful_fireball
                         perform_powerful_fireball(self, self.game, self.game.player)
                     else:
                         player = self.game.player
                         p_dx = player.x - self.x
                         p_dy = player.y - self.y
                         self.game.projectiles.append(
                            Projectile(self.x, self.y, direction=(p_dx, p_dy), speed=6, damage=self.damage, owner_type="enemy", texture=None, visual_type="ARROW", color=(150, 50, 255))
                         )
                     self.last_attack_time = current_time

            # Action 6: Utility (Summon / Dash / Shield)
            elif self.current_ai_action == 6:
                if self.phase == 1:
                     pass # Disabled in Phase 1
                     
                elif self.phase == 2:
                     if current_time - self.ability_cooldowns['dash'] > 5000:
                         self.is_dashing = True
                         self.dash_timer = current_time
                         self.dash_target = (self.game.player.x, self.game.player.y)
                         self.ability_cooldowns['dash'] = current_time
                         
                elif self.phase == 3:
                     # Phase 3: Try Shield -> Else Summon -> Else Dash
                     if current_time - self.ability_cooldowns['shield'] > 10000:
                         self.is_shielded = True
                         self.shield_timer = current_time
                         self.ability_cooldowns['shield'] = current_time
                         debug.log("AI Phase 3: Shield")
                     elif current_time - self.ability_cooldowns['summon'] > 3500:
                        from entities.boss.mechanics import perform_summon
                        perform_summon(self, self.game)
                        self.ability_cooldowns['summon'] = current_time
                        debug.log("AI Phase 3: Summon")
                     elif current_time - self.ability_cooldowns['dash'] > 4000:
                         self.is_dashing = True
                         self.dash_timer = current_time
                         self.dash_target = (self.game.player.x, self.game.player.y)
                         self.ability_cooldowns['dash'] = current_time
                         debug.log("AI Phase 3: Dash")

            # Action 7: Heavy (Gravity / Bullet Hell)
            elif self.current_ai_action == 7:
                 if self.phase == 1:
                    if current_time - self.ability_cooldowns['gravity'] > 6000:
                        from entities.boss.mechanics import perform_gravity_smash
                        perform_gravity_smash(self, self.game.player)
                        self.ability_cooldowns['gravity'] = current_time
                        
                 elif self.phase == 3:
                    # Phase 3: Try Bullet Hell -> Else Gravity
                    if current_time - self.ability_cooldowns.get('bullet_hell', 0) > 8000:
                        from entities.boss.mechanics import perform_bullet_hell
                        perform_bullet_hell(self, self.game)
                        self.ability_cooldowns['bullet_hell'] = current_time
                        debug.log("AI Phase 3: Bullet Hell")
                    elif current_time - self.ability_cooldowns['gravity'] > 5000:
                        from entities.boss.mechanics import perform_gravity_smash
                        perform_gravity_smash(self, self.game.player)
                        self.ability_cooldowns['gravity'] = current_time
                        debug.log("AI Phase 3: Gravity")

        else:
            # Fallback (Non-AI)
            if hasattr(target_pos_or_flow_field, 'get_vector'):
                if not hasattr(self, 'behavior') or self.behavior is None:
                    from entities.behaviors import EnemyBehaviors
                    self.behavior = EnemyBehaviors.get_behavior(getattr(self, 'behavior_name', 'melee'))
                direction_tuple = self.behavior(self, target_pos_or_flow_field, entities)
                dx = direction_tuple[0] * self.speed; dy = direction_tuple[1] * self.speed
                self._try_heal(entities)
            else:
                target = pygame.math.Vector2(target_pos_or_flow_field)
                cur = pygame.math.Vector2(self.x, self.y)
                if cur.distance_to(target) > 0:
                    direction = (target - cur).normalize()
                    dx = direction.x * self.speed; dy = direction.y * self.speed
        
        # Apply Movement
        bounds = (0, 0, self.game.world.width * CELL_SIZE, self.game.world.height * CELL_SIZE)
        new_x = self.x + dx
        if not check_collision(new_x, self.y, self.w, self.h, bounds, self.game.world): self.x = new_x
        new_y = self.y + dy
        if not check_collision(self.x, new_y, self.w, self.h, bounds, self.game.world): self.y = new_y