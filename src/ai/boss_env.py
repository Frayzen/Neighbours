import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from core.game import Game
from entities.enemy import Enemy
from core.registry import Registry

class BossFightEnv(gym.Env):
    def __init__(self):
        super(BossFightEnv, self).__init__()
        
        # Initialize Game (Headless-ish? Pygame needs a video system usually)
        # We assume SDL_VIDEODRIVER is handled externally if needed, or we just let it open a window.
        self.game = Game()
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
        # We access gridObjects directly.
        # Filter out enemies
        self.game.gridObjects = [obj for obj in self.game.gridObjects if obj == self.game.player]
        self.game.enemies = [] 
        
        # Force Spawn Boss ("JörnBoss")
        # Center of Map
        boss_x = self.game.world.width * 32 // 2
        boss_y = self.game.world.height * 32 // 2
        
        # Ensure 'JörnBoss' config exists or fallback
        # Ideally it is loaded from config, but we can trust the setup or handle missing logic.
        from entities.boss.joern import JoernBoss
        self.boss = JoernBoss(self.game, boss_x, boss_y)
        self.boss.ai_controlled = True
        self.game.gridObjects.append(self.boss)
        
        # Training Balance: Cap HP to 1000 to speed up episodes
        self.boss.health = 1000
        self.boss.max_health = 1000 # Optional: Adjust max so bar looks right or keep 5000? 
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

    def step(self, action):
        # Apply Action
        if self.boss:
            self.boss.set_ai_action(action)
            
        # Determine player movement keys based on bot logic
        keys = self._get_bot_keys()
        
        # Monkey patch pygame.key.get_pressed to simulate player input
        # We need a proper sequence or object that allows indexing
        # pygame.key.get_pressed returns a ScancodeWrapper which is tuple-like.
        # We can use a simple list of 0s and 1s, sized 512 (or ScancodeWrapper length).
        
        original_get_pressed = pygame.key.get_pressed
        
        def mock_get_pressed():
            return keys
            
        pygame.key.get_pressed = mock_get_pressed
        
        try:
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
        # Encouraging Aggression: 2.0x for damage dealt
        # Existential Penalty: -0.05 per step to force quick kills
        reward = (dmg_dealt * 2.0) - (dmg_taken * 1.0)
        reward -= 0.05
        
        if current_boss_hp <= 0:
            reward += 100 # Bonus for killing boss
        
        if current_player_hp <= 0:
            reward -= 50 # Penalty for dying
            
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
