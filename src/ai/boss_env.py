import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from collections import defaultdict
from core.game import Game
from entities.enemy import Enemy
from core.registry import Registry
from config.settings import CELL_SIZE
from config.ai_weights import (
    REWARD_DMG_DEALT_MULTIPLIER,
    REWARD_DMG_TAKEN_MULTIPLIER,
    REWARD_STEP_PENALTY,
    REWARD_WHIFF_PENALTY,
    REWARD_DISTANCE_BONUS,
    REWARD_WIN,
    REWARD_LOSS,
    DISTANCE_BONUS_MIN,
    DISTANCE_BONUS_MAX
)

class BossFightEnv(gym.Env):
    def __init__(self, headless=False, difficulty=1):
        super(BossFightEnv, self).__init__()
        
        self.difficulty = difficulty # 1: Stand, 2: Run, 3: Kite/Attack
        print(f"BossFightEnv Initialized (Difficulty: {difficulty})")
        
        # Initialize Game (Headless-ish? Pygame needs a video system usually)
        # We assume SDL_VIDEODRIVER is handled externally if needed, or we just let it open a window.
        self.game = Game(headless=headless)
        self.game.paused = False
        
        # Actions: 0: Idle, 1-4: Move, 5: Attack, 6: Ability 1, 7: Ability 2
        self.action_space = spaces.Discrete(8)
        
        # Observation: [BossX, BossY, PlayerX, PlayerY, BossHP, PlayerHP, Phase, CD1, CD2]
        # We use a Box with shape (9,)
        # Normalized values are preferred but we define bounds loosely here.
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(9,), dtype=np.float32)
        
        self.boss = None
        self.prev_boss_hp = 100
        self.prev_player_hp = 100
        
        # For simulation
        self.boss_start_hp = 0
        
        # Stats for Overlay
        self.episode_count = 0
        self.total_reward = 0
        self.step_count = 0
        self.font = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.episode_count += 1
        self.total_reward = 0
        self.step_count = 0
        
        # Reset Game Logic
        self.game.restart_game()
        
        # Clear existing enemies
        # 1. NUKE THE "STUPID BOSS" (Clear natural spawns)
        self.game.world.spawn_points = []
        
        # 2. Filter existing entities
        self.game.gridObjects = [obj for obj in self.game.gridObjects if obj == self.game.player]
        self.game.enemies = [] 
        
        # 3. FIX SPAWN POSITIONS (Use CELL_SIZE, not 32)
        center_x_pix = (self.game.world.width * CELL_SIZE) // 2
        center_y_pix = (self.game.world.height * CELL_SIZE) // 2
        
        # Spawn Boss in the middle
        from entities.boss.joern import JoernBoss
        self.boss = JoernBoss(self.game, center_x_pix, center_y_pix)
        self.boss.ai_controlled = True
        self.game.gridObjects.append(self.boss)
        
        # Spawn Player slightly to the left (200px away)
        self.game.player.x = center_x_pix - 200
        self.game.player.y = center_y_pix
        
        # Training Balance: Cap HP to 1000 to speed up episodes
        self.boss.health = 3000
        self.boss.max_health = 3000 # Optional: Adjust max so bar looks right or keep 5000? 
        # Better to just set health to 1000, keep max 5000 if we want to simulate "portion of fight" 
        # OR set both to 1000 to simulate a full fight with less HP.
        # User said "set self.boss.health = 1000".
        
        self.boss_start_hp = self.boss.max_health
        
        # Reset Player
        self.game.player.x = 100
        self.game.player.y = 100
        self.game.player.health = self.game.player.max_health
        self.game.player.active_effects = []
        
        self.prev_boss_hp = self.boss.health
        self.prev_player_hp = self.game.player.health
        
        return self._get_obs(), {}

    def render(self):
        # Delegate to game renderer
        if not self.game.renderer.screen:
             # Force init screen if not present (headless mode might skip it)
             pygame.display.set_mode((self.game.world.width*32, self.game.world.height*32))
             self.game.renderer = None # Reload
             from core.renderer import GameRenderer
             self.game.renderer = GameRenderer(self.game)

        # Update visuals
        self.game.camera.update(self.game.player)
        self.game.renderer.draw(self.game.camera)
        
        self._render_stats_overlay()
        
        pygame.display.flip()
        
    def _render_stats_overlay(self):
        if not self.font:
            self.font = pygame.font.SysFont("Arial", 16)
            
        screen = pygame.display.get_surface()
        if not screen: return

        info = [
            f"Episode: {self.episode_count}",
            f"Step: {self.step_count}",
            f"Total Reward: {self.total_reward:.2f}",
            f"Boss HP: {self.boss.health:.0f}/{self.boss.max_health:.0f}",
            f"Player HP: {self.game.player.health:.0f}/{self.game.player.max_health:.0f}"
        ]
        
        x = 10
        y = 10
        bg_surface = pygame.Surface((200, 120))
        bg_surface.set_alpha(180)
        bg_surface.fill((0, 0, 0))
        screen.blit(bg_surface, (5, 5))
        
        for line in info:
            text = self.font.render(line, True, (255, 255, 255))
            screen.blit(text, (x, y))
            y += 20

    def _get_bot_action(self):
        # Difficulty 1: Stand Still
        if self.difficulty == 1:
             return 0
             
        player = self.game.player
        boss = self.boss
        if not boss: return 0
        
        dx = boss.x - player.x
        dy = boss.y - player.y
        dist_sq = dx*dx + dy*dy
        
        action = 0 
        min_dist = 250
        
        if dist_sq < min_dist**2:
             # Run away
             vx, vy = -dx, -dy # Vector from boss to player (inverted) -> Player runs away from boss
             # Wait, dx = boss - player.
             # Player to Boss vector = (boss.x - player.x, boss.y - player.y) = (dx, dy)
             # To run AWAY, Player should move -dx, -dy? 
             # No, if Boss is at (10,10) and Player at (0,0). Boss-Player = (10,10).
             # Player moving (-10,-10) goes to (-10,-10), away from (10,10). Correct.
             
             vx, vy = -dx, -dy
             if abs(vx) > abs(vy):
                 action = 4 if vx > 0 else 3
             else:
                 action = 2 if vy > 0 else 1
                 
        # Difficulty 3: Kite
        if self.difficulty >= 3:
             if dist_sq < min_dist**2:
                 pass
             elif dist_sq > 450**2:
                 # Move closer
                 vx, vy = dx, dy
                 if abs(vx) > abs(vy):
                     action = 4 if vx > 0 else 3
                 else:
                     action = 2 if vy > 0 else 1
             else:
                 action = 5 # Attack
                 
        return action

    def step(self, action):
        # Apply Boss Action
        if self.boss:
            self.boss.set_ai_action(action)
            
        # Apply Player Bot Action
        bot_action = self._get_bot_action()
        self.game.player.set_ai_action(bot_action)
        
        # Ensure AI Control is ON for Player (Safety)
        self.game.player.ai_controlled = True

        original_get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: defaultdict(int) # Safe for any key index
        
        try:
            # Frame Skipping: Run 4 frames per action
            for _ in range(4):
                self.game.logic.update()
        except Exception as e:
            print(f"Error during logic update: {e}")
        finally:
            pygame.key.get_pressed = original_get_pressed
            
        # Handle visualization events (like window close) to prevent freezing if rendered
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        
        # Render if configured to do so (we call it manually here if we want to force see it, otherwise reliant on gym loop)
        # self.render() 
        
        # Calculate Reward
        current_boss_hp = self.boss.health if self.boss else 0
        current_player_hp = self.game.player.health
        
        dmg_dealt = self.prev_boss_hp - current_boss_hp
        dmg_taken = self.prev_player_hp - current_player_hp
        
        # Reward Function
        # We want to maximize damage dealt and minimize damage taken.
        # Encouraging Aggression
        # Existential Penalty: per step to force quick kills
        reward = (dmg_dealt * REWARD_DMG_DEALT_MULTIPLIER) - (dmg_taken * REWARD_DMG_TAKEN_MULTIPLIER)
        reward -= REWARD_STEP_PENALTY
        
        # Whiff Punishment (If attacked but dealt no damage)
        # Action 5 is Attack
        if action == 5 and dmg_dealt <= 0:
            reward -= REWARD_WHIFF_PENALTY
            
        # Distance Reward
        # Encourage staying within effective range but not hugging
        if self.boss:
             dx = self.game.player.x - self.boss.x
             dy = self.game.player.y - self.boss.y
             dist = (dx**2 + dy**2)**0.5
             if DISTANCE_BONUS_MIN < dist < DISTANCE_BONUS_MAX:
                 reward += REWARD_DISTANCE_BONUS
        
        if current_boss_hp <= 0:
            reward += REWARD_WIN # Bonus for killing boss
        
        if current_player_hp <= 0:
            reward -= REWARD_LOSS # Penalty for dying
            
        self.total_reward += reward
        self.step_count += 1
        
        # Update prev
        self.prev_boss_hp = current_boss_hp
        self.prev_player_hp = current_player_hp
        
        # Check Done
        terminated = False
        if current_boss_hp <= 0 or current_player_hp <= 0:
            terminated = True
            
        truncated = False 
        
        info = {}
        
        return self._get_obs(), reward, terminated, truncated, info

    def _get_obs(self):
        if not self.boss or self.boss not in self.game.gridObjects:
            # If boss died and removed, return zeros or last state with 0 hp
             return np.zeros(9, dtype=np.float32)

        # Normalize logic
        w = max(1, self.game.world.width * 32)
        h = max(1, self.game.world.height * 32)
        
        bx = self.boss.x / w
        by = self.boss.y / h
        px = self.game.player.x / w
        py = self.game.player.y / h
        bhp = self.boss.health / max(1, self.boss.max_health)
        php = self.game.player.health / max(1, self.game.player.max_health)
        phase = getattr(self.boss, 'phase', 1) / 3.0
        
        # Cooldowns
        cur = pygame.time.get_ticks()
        
        def get_cd_norm(name, duration):
            last = self.boss.ability_cooldowns.get(name, 0)
            if cur - last > duration:
                return 0.0 # Ready
            else:
                return (last + duration - cur) / duration # 1.0 = Just used, 0.0 = Ready

        cd1 = get_cd_norm("dash", 5000) # Assuming 5s
        cd2 = get_cd_norm("shield", 10000) # Assuming 10s
        
        return np.array([bx, by, px, py, bhp, php, phase, cd1, cd2], dtype=np.float32)

    def _get_bot_keys(self):
        class MockKeys:
            def __init__(self, key_dict):
                self.key_dict = key_dict
            def __getitem__(self, key):
                # Returns 1 if key is in dict, else 0
                return self.key_dict.get(key, 0)
            def __iter__(self):
                return iter(self.key_dict.values())
            def __len__(self):
                return 512 # valid dummy length
                
        key_dict = {}
        
        if not self.boss: return MockKeys(key_dict)
        
        player = self.game.player
        boss = self.boss
        
        dist_sq = (player.x - boss.x)**2 + (player.y - boss.y)**2
        
        dx = 0
        dy = 0
        
        # Simple Logic: Run away if < 200px (approx 6 tiles), else maybe move closer if > 400px?
        min_dist = 200
        max_dist = 400
        
        if dist_sq < min_dist**2:
            # Run away
            if player.x < boss.x: dx = -1
            else: dx = 1
            if player.y < boss.y: dy = -1
            else: dy = 1
        elif dist_sq > max_dist**2:
            # Move Closer (Prevent Camping)
            if player.x < boss.x: dx = 1
            else: dx = -1
            if player.y < boss.y: dy = 1
            else: dy = -1
            
        # Map dx, dy into keys
        if dy < 0: key_dict[pygame.K_w] = 1
        if dy > 0: key_dict[pygame.K_s] = 1
        if dx < 0: key_dict[pygame.K_a] = 1
        if dx > 0: key_dict[pygame.K_d] = 1
        
        return MockKeys(key_dict)
