import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import traceback # Added for debuggingsys
import os
import sys
from collections import defaultdict

# Add src directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game import Game
from entities.enemy import Enemy
from entities.player import Player
from config.settings import CELL_SIZE
try:
    from stable_baselines3 import PPO
except ImportError:
    PPO = None

class DuelEnv(gym.Env):
    def __init__(self, mode="TRAIN_BOSS", human_opponent=False, headless=False, difficulty=1):
        super(DuelEnv, self).__init__()
        
        self.mode = mode # "TRAIN_BOSS" or "TRAIN_PLAYER"
        self.human_opponent = human_opponent
        self.headless = headless
        self.difficulty = difficulty # 1: Stand Still, 2: Run Away, 3: Kite/Attack
        print(f"DuelEnv Initialized in mode: {self.mode} (Headless: {headless}, Difficulty: {difficulty})")
        
        # Initialize Game
        self.game = Game(headless=self.headless)
        self.game.paused = False
        
        # Actions: 0: Idle, 1-4: Move, 5: Attack, 6: Ability 1, 7: Ability 2
        # Both Boss and Player support 0-7 via set_ai_action
        self.action_space = spaces.Discrete(8)
        
        # Observation: [BossX, BossY, PlayerX, PlayerY, BossHP, PlayerHP, Phase, CD1, CD2]
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(9,), dtype=np.float32)
        
        self.boss = None
        self.prev_boss_hp = 100
        self.prev_player_hp = 100
        
        # Stats
        self.episode_count = 0
        self.total_reward = 0
        self.step_count = 0
        self.win_history = [] # 1 for Agent Win, 0 for Loss
        self.font = None
        
        # Load Opponent Model
        self.opponent_model = None
        self.opponent_model_path = ""
        
        if self.mode == "TRAIN_BOSS":
            # Opponent is Player
            self.opponent_model_path = "player_ai_v1" # Expected name
        elif self.mode == "TRAIN_PLAYER":
            # Opponent is Boss
            self.opponent_model_path = "joern_boss_ai_v1" # Expected name
            
        if PPO and self.opponent_model_path:
            if os.path.exists(self.opponent_model_path + ".zip"):
                try:
                    self.opponent_model = PPO.load(self.opponent_model_path)
                    print(f"Loaded opponent model: {self.opponent_model_path}")
                except Exception as e:
                    print(f"Failed to load opponent model {self.opponent_model_path}: {e}")
            else:
                print(f"Opponent model not found: {self.opponent_model_path}. Using fallback/script.")
                
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.episode_count += 1
        self.total_reward = 0
        self.step_count = 0
        self.last_damage_step = 0 # For Stalemate logic
        
        # 1. Reset Game
        self.game.restart_game()
        
        # 2. NUKE THE "STUPID BOSS" (Clear natural spawns)
        # This prevents the level loader's JörnBoss from spawning
        self.game.world.spawn_points = []
        
        # 3. Filter existing entities (just in case)
        self.game.gridObjects = [obj for obj in self.game.gridObjects if obj == self.game.player]
        self.game.enemies = [] 
        
        # 4. FIX SPAWN POSITIONS (Use CELL_SIZE, not 32)
        # Center of the 100x100 grid
        center_x_pix = (self.game.world.width * CELL_SIZE) // 2
        center_y_pix = (self.game.world.height * CELL_SIZE) // 2
        
        # Spawn Boss in the middle
        from entities.boss.joern import JoernBoss
        self.boss = JoernBoss(self.game, center_x_pix, center_y_pix)
        self.game.gridObjects.append(self.boss)
        
        # Spawn Player slightly to the left (200px away) so they don't overlap instantly
        self.game.player.x = center_x_pix - 200
        self.game.player.y = center_y_pix
        
        # 5. Configure Stats
        self.boss.health = 1000
        self.boss.max_health = 1000
        
        self.game.player.health = self.game.player.max_health
        
        # Configure AI Control flags based on MODE and MODEL availability
        
        if self.mode == "TRAIN_BOSS":
            # Agent controls Boss
            self.boss.ai_controlled = True
            
            # Formally, Player AI is controlled if we have a model or if we want to script it via set_ai_action
            # If no model, we fallback to our script.
            # Our script in boss_env used keys. DuelEnv should ideally use set_ai_action for both for consistency.
            if not self.human_opponent:
                self.game.player.ai_controlled = True 
            else:
                self.game.player.ai_controlled = False 
            
        elif self.mode == "TRAIN_PLAYER":
            # Agent controls Player
            self.game.player.ai_controlled = True
            
            # Opponent (Boss)
            if self.opponent_model:
                self.boss.ai_controlled = True
            else:
                # If no model, let standard AI control Boss?
                # Standard AI uses update() logic and ignores set_ai_action if ai_controlled=False.
                # But to start standard AI, we just need ai_controlled=False.
                self.boss.ai_controlled = False

        self.prev_boss_hp = self.boss.health
        self.prev_player_hp = self.game.player.health
        
        return self._get_obs(), {}

    def step(self, action):
        obs = self._get_obs()
        
        # Apply Actions
        if self.mode == "TRAIN_BOSS":
             # Agent controls Boss
             if self.boss: self.boss.set_ai_action(action)
             
             # Opponent (Player)
             if not self.human_opponent and not self.opponent_model:
                 # Curriculum Bot
                 bot_action = self._get_bot_action()
                 self.game.player.set_ai_action(bot_action)
             elif self.opponent_model:
                 # Trained Model Opponent
                 p_act, _ = self.opponent_model.predict(obs)
                 self.game.player.set_ai_action(int(p_act))
                 
        elif self.mode == "TRAIN_PLAYER":
             # Agent controls Player
             self.game.player.set_ai_action(action)
             
             # Opponent (Boss)
             if not self.opponent_model:
                 # Standard AI uses behavior trees (better).
                 pass
             else:
                 # Trained Model Opponent
                 b_act, _ = self.opponent_model.predict(obs)
                 if self.boss: self.boss.set_ai_action(int(b_act))
                 
        # Determine player movement keys based on bot logic
        # REMOVED: Legacy _get_bot_keys logic replaced by set_ai_action
        
        # Monkey patch pygame.key.get_pressed to simulate player input
        # No longer needed if ai_controlled works, but keeping empty for safety
        original_get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: defaultdict(int) # Safe for any key index
        
        try:
            # Frame Skipping: Run 4 frames per action
            for _ in range(4):
                self.game.logic.update()
        except Exception as e:
            print(f"Error during logic update: {e}")
            traceback.print_exc()
            
        finally:
            pygame.key.get_pressed = original_get_pressed
        
        # Handle Pygame Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            
            # Forward events if human playing
            if self.human_opponent and self.game:
                self.game.logic.handle_event(event)

        # 4. Calculate Rewards
        current_boss_hp = self.boss.health if self.boss else 0
        current_player_hp = self.game.player.health
        
        dmg_dealt_to_boss = self.prev_boss_hp - current_boss_hp
        dmg_dealt_to_player = self.prev_player_hp - current_player_hp
        
        reward = 0
        
        if self.mode == "TRAIN_BOSS":
            # Reward Boss
            # + Damage Dealt to Player, - Damage Taken
            reward = (dmg_dealt_to_player * 2.0) - (dmg_dealt_to_boss * 1.0)
            reward -= 0.05
            dmg_dealt = dmg_dealt_to_player
            dmg_taken = dmg_dealt_to_boss
        elif self.mode == "TRAIN_PLAYER":
            dmg_dealt = dmg_dealt_to_boss
            dmg_taken = dmg_dealt_to_player
            
        # Reward Function
        # We want to maximize damage dealt and minimize damage taken.
        # Encouraging Aggression: 2.0x for damage dealt
        # Existential Penalty: -0.05 per step to force quick kills
        reward = (dmg_dealt * 2.0) - (dmg_taken * 1.0)
        reward -= 0.05
        
        # Whiff Punishment & Distance Reward
        if self.mode == "TRAIN_BOSS" and self.boss:
            # Controlling Boss
             if action == 5 and dmg_dealt <= 0:
                 reward -= 0.2
             
             dist = ((self.game.player.x - self.boss.x)**2 + (self.game.player.y - self.boss.y)**2)**0.5
             if 150 < dist < 450:
                 reward += 0.01
                 
        elif self.mode == "TRAIN_PLAYER":
            # Controlling Player
            # Action 5 might be attack for player too?
             if action == 5 and dmg_dealt <= 0: # Assuming player dmg_dealt is to boss (dmg_dealt var is boss loss?)
                 # In TRAIN_PLAYER, we want to MAXIMIZE Boss Damage Taken.
                 # dmg_dealt = prev_boss_hp - cur_boss_hp. So positive dmg_dealt is good.
                 reward -= 0.2
             
             dist = ((self.game.player.x - self.boss.x)**2 + (self.game.player.y - self.boss.y)**2)**0.5
             if 150 < dist < 450:
                 reward += 0.01

        if current_boss_hp <= 0:
            if self.mode == "TRAIN_BOSS": reward -= 50 # Boss Died (Bad)
            else: reward += 100 # Boss Died (Good for Player)
        
        if current_player_hp <= 0:
            if self.mode == "TRAIN_BOSS": reward += 100 # Player Died (Good for Boss)
            else: reward -= 50 # Player Died (Bad)         
        self.total_reward += reward
        self.step_count += 1
        
        self.prev_boss_hp = current_boss_hp
        self.prev_player_hp = current_player_hp
        
        # 5. Check Done
        terminated = False
        truncated = False
        winner = None # 1 if Agent wins, 0 if Opponent wins (conceptually)
        # Actually win_history usually tracks 1=Win (for Agent), 0=Loss.
        
        if current_boss_hp <= 0: 
            terminated = True
            # Boss Died
            if self.mode == "TRAIN_BOSS": winner = 0 # Loss
            else: winner = 1 # Win (Player Agent)
            
        if current_player_hp <= 0:
            terminated = True
            # Player Died
            if self.mode == "TRAIN_BOSS": winner = 1 # Win (Boss Agent)
            else: winner = 0 # Loss
            
        # STALEMATE BREAKER
        # If no damage dealt for N steps, end game
        if dmg_dealt != 0 or dmg_taken != 0:
            self.last_damage_step = self.step_count
            
        if self.step_count - self.last_damage_step > 500:
            terminated = True
            # Stalemate Penalty
            reward -= 0.1
            truncated = True # Or just terminated? Truncated is better for time limit.
            
        if terminated and winner is not None:
             self.win_history.append(winner)
             
        # Scale Reward for Stability (PPO likes -1 to 1)
        reward = reward / 100.0
             
        return self._get_obs(), reward, terminated, truncated, {}

    def _get_obs(self):
        # Same observation logic as BossFightEnv for compatibility
        if not self.boss or self.boss not in self.game.gridObjects:
             return np.zeros(9, dtype=np.float32)

        w = max(1, self.game.world.width * 32)
        h = max(1, self.game.world.height * 32)
        
        bx = self.boss.x / w
        by = self.boss.y / h
        px = self.game.player.x / w
        py = self.game.player.y / h
        bhp = self.boss.health / max(1, self.boss.max_health)
        php = self.game.player.health / max(1, self.game.player.max_health)
        phase = getattr(self.boss, 'phase', 1) / 3.0
        
        cur = pygame.time.get_ticks()
        def get_cd_norm(name, duration):
            last = self.boss.ability_cooldowns.get(name, 0)
            if cur - last > duration: return 0.0
            else: return (last + duration - cur) / duration

        cd1 = get_cd_norm("dash", 5000)
        cd2 = get_cd_norm("shield", 10000)
        
        return np.array([bx, by, px, py, bhp, php, phase, cd1, cd2], dtype=np.float32)

        return 0 # Idle

    def render(self):
        if not getattr(self.game, 'screen', None):
             pygame.display.set_mode((self.game.world.width*32, self.game.world.height*32))
             from core.renderer import GameRenderer
             self.game.renderer = GameRenderer(self.game)

        self.game.camera.update(self.game.player)
        self.game.renderer.draw(self.game.camera)
        
        self._render_stats_overlay()
        self._render_graph()
        
        pygame.display.flip()

    def _render_stats_overlay(self):
        if not self.font:
            self.font = pygame.font.SysFont("Arial", 16)
        screen = pygame.display.get_surface()
        
        info = [
            f"Mode: {self.mode}",
            f"Episode: {self.episode_count}",
            f"Win Rate: {np.mean(self.win_history[-50:]):.2f}" if self.win_history else "Win Rate: N/A",
            f"Boss HP: {self.boss.health:.0f}",
            f"Player HP: {self.game.player.health:.0f}"
        ]
        
        y = 10
        for line in info:
             text = self.font.render(line, True, (255, 255, 255))
             screen.blit(text, (10, y))
             y += 20
             
    def _render_graph(self):
        # Draw win history graph bottom right
        # win_history is list of 0s and 1s.
        if len(self.win_history) < 2: return
        
        screen = pygame.display.get_surface()
        w, h = screen.get_size()
        
        graph_w = 200
        graph_h = 100
        x_base = w - graph_w - 10
        y_base = h - graph_h - 10
        
        # Draw Background
        pygame.draw.rect(screen, (0, 0, 0, 150), (x_base, y_base, graph_w, graph_h))
        pygame.draw.rect(screen, (255, 255, 255), (x_base, y_base, graph_w, graph_h), 1)
        
        # Plot Moving Average of last 50
        # If we plot raw 0/1 it's messy. Moving average is better.
        points = []
        data = self.win_history[-100:] # Last 100 episodes
        
        # Calculating moving average for smoother graph?
        # Or just plot raw wins as vertical bars? 
        # User said "pygame.draw.lines to visualize the win_history list".
        # Let's plot the "Win Rate" over time.
        
        vals = []
        running_sum = 0
        window = 10
        
        for i in range(len(self.win_history)):
             # Calculate win rate for last 10 games at point i
             start = max(0, i - window)
             subset = self.win_history[start:i+1]
             rate = sum(subset) / len(subset)
             vals.append(rate)
             
        # Slice to last N to fit graph
        display_vals = vals[-100:]
        
        step_x = graph_w / max(1, len(display_vals) - 1)
        
        for i, val in enumerate(display_vals):
            px = x_base + i * step_x
            py = y_base + graph_h - (val * graph_h) # 1.0 is top, 0.0 is bottom
            points.append((px, py))
            
        if len(points) > 1:
            pygame.draw.lines(screen, (0, 255, 0), False, points, 2)

    def _get_bot_action(self):
        """
        Simple fallback AI for the Player when no model is loaded.
        """
        if not self.boss: return 0
        
        px, py = self.game.player.x, self.game.player.y
        bx, by = self.boss.x, self.boss.y
        
        dist_sq = (px - bx)**2 + (py - by)**2
        
        # 1. Attack Logic (Simple Spam)
        if np.random.rand() < 0.2: # 20% chance to attack per decision
            return 5
            
        # 2. Movement Logic
        dx, dy = 0, 0
        min_dist = 200 ** 2
        
        if dist_sq < min_dist:
            # Run Away
            if px < bx: dx = -1
            else: dx = 1
            if py < by: dy = -1
            else: dy = 1
        else:
            # Move Closer
            if px < bx: dx = 1
            else: dx = -1
            if py < by: dy = 1
            else: dy = -1
            
        # Convert dx/dy to Action Index
        if dy < 0: return 1 # Up
        if dy > 0: return 2 # Down
        if dx < 0: return 3 # Left
        if dx > 0: return 4 # Right
        
        return 0 # Idle
