import pygame
from entities.enemies.enemy import Enemy
from core.debug import debug
from config.settings import CELL_SIZE

class Boss(Enemy):
    def __init__(self, game, x, y, enemy_type="JoernBoss", modifiers=None):
        super().__init__(game, x, y, enemy_type, modifiers)
        
        # Boss specific stats
        self.phase = 1
        self.ability_cooldowns = { "summon": 0, "dash": 0, "shield": 0, "gravity": 0 }
        self.is_shielded = False
        self.is_dashing = False
        self.dash_timer = 0
        self.shield_timer = 0
        self.dash_target = (0,0)

    def take_damage(self, amount):
        if self.is_shielded:
            self.game.damage_texts.spawn(self.x, self.y - 20, "BLOCKED", color=(200, 200, 255))
            return
        super().take_damage(amount)

    def die(self):
        super().die()
        if self.enemy_type == "JoernBoss":
            self.game.trigger_victory()

    def update(self, target_pos_or_flow_field, entities=None):
        current_time = pygame.time.get_ticks()

        # Boss Phase Logic
        if self.enemy_type == "JoernBoss":
            hp_percent = self.health / self.max_health
            
            # Phase 2 check
            if hp_percent < 0.66 and self.phase < 2:
                self.phase = 2
                self.color = (255, 100, 0) # Orange-ish for Phase 2
                debug.log(f"{self.enemy_type} entered Phase 2!")
                self._load_phase_assets(2)
                
            # Phase 3 check
            if hp_percent < 0.33 and self.phase < 3:
                self.phase = 3
                self.color = (255, 0, 0) # Red for Phase 3
                debug.log(f"{self.enemy_type} entered Phase 3!")

                # Trigger Final Ember Ability
                from entities.boss_mechanics import perform_The_Final_Ember
                perform_The_Final_Ember(self, self.game)
                self._load_phase_assets(3)

            # Need to import constants for timeouts
            from entities.boss_mechanics import SHIELD_DURATION, DASH_DURATION, DASH_SPEED_MULTIPLIER

            # Handle One-time durations (Shield, Dash Reset)
            if self.is_shielded:
                if current_time - self.shield_timer > SHIELD_DURATION:
                    self.is_shielded = False
                    from core.registry import Registry
                    self.color = Registry.get_enemy_config(self.enemy_type).get("color", (255,0,0))
                    # Restore phase color
                    if self.phase == 2: self.color = (255, 100, 0)
                    if self.phase == 3: self.color = (255, 0, 0)

            if getattr(self, 'is_dashing', False):
                 if current_time - self.dash_timer > DASH_DURATION:
                     self.is_dashing = False

            # Dash Movement Override
            if getattr(self, 'is_dashing', False):
                 # Move towards dash target
                 tx, ty = self.dash_target
                 dx = tx - self.x
                 dy = ty - self.y
                 dist = (dx**2 + dy**2)**0.5
                 
                 # Speed multiplier
                 move_speed = self.speed * DASH_SPEED_MULTIPLIER
                 
                 if dist < move_speed:
                     self.x = tx
                     self.y = ty
                     self.is_dashing = False
                 else:
                     self.x += (dx/dist) * move_speed
                     self.y += (dy/dist) * move_speed
                 
                 self._apply_movement(0, 0) # Updates checks but mostly manual placement above
                 return

        # Normal Behavior Update
        super().update(target_pos_or_flow_field, entities)

    def _load_phase_assets(self, phase_num):
        """
        Loads texture and animation CSV for the given phase.
        Expects keys like 'texture_phase_2', 'animation_csv_phase_2' in config.
        """
        from core.registry import Registry
        import os
        from config.animation_constants import ANIM_IDLE
        
        config = Registry.get_enemy_config(self.enemy_type)
        if not config: return

        # Texture Key
        tex_key = f"texture_phase_{phase_num}"
        p_path = config.get(tex_key)
        
        # Animation Key
        anim_key = f"animation_csv_phase_{phase_num}"
        a_path = config.get(anim_key)
        
        if p_path:
             try:
                 full_path = os.path.normpath(os.path.join("src/config", p_path))
                 if os.path.exists(full_path):
                     self.texture = pygame.image.load(full_path).convert_alpha()
                     debug.log(f"Loaded Phase {phase_num} texture from {full_path}")
                     
                     # Also try to load animation if provided
                     if a_path:
                         full_anim_path = os.path.normpath(os.path.join("src/config", a_path))
                         if self.animator.load_from_paths(full_anim_path, full_path):
                             self.use_animation = True
                             self.animator.play(ANIM_IDLE) # Reset to idle on phase change
                             debug.log(f"Loaded Phase {phase_num} animations from {full_anim_path}")
                 else:
                     debug.log(f"Phase {phase_num} texture path not found: {full_path}")
             except Exception as e:
                 print(f"Failed to load Phase {phase_num} assets: {e}")
