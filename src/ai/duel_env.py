import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import traceback # Added for debuggingsys
import os
import sys
import math
from collections import defaultdict

# Add src directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game import Game
from entities.enemy import Enemy
from entities.player import Player
from entities.player import Player
from config.settings import CELL_SIZE, GRID_WIDTH, GRID_HEIGHT
from ai.vision import cast_wall_ray, cast_entity_ray
try:
    from stable_baselines3 import PPO
except ImportError:
    PPO = None

from config.ai_weights import (
    REWARD_DMG_DEALT_MULTIPLIER,
    REWARD_DMG_TAKEN_MULTIPLIER,
    REWARD_STEP_PENALTY,
    REWARD_WHIFF_PENALTY,
    REWARD_WALL_COLLISION_PENALTY,
    REWARD_STALEMATE_PENALTY,
    REWARD_DISTANCE_BONUS,
    REWARD_WIN,
    REWARD_LOSS,
    DISTANCE_BONUS_MIN,
    DISTANCE_BONUS_MAX
)

class DuelEnv(gym.Env):
    def __init__(self, mode="TRAIN_BOSS", human_opponent=False, headless=False, difficulty=1):
        super(DuelEnv, self).__init__()
        
        self.mode = mode # "TRAIN_BOSS" or "TRAIN_PLAYER"
        self.human_opponent = human_opponent
        self.headless = headless
        self.difficulty = difficulty # 1: Stand Still, 2: Run Away, 3: Kite/Attack
        
        # Frame Skip Logic
        # If Human Playing OR Watching (Not Headless), run 1x speed (frame_skip = 1)
        # If Training (Headless and AI vs AI), run 4x speed (frame_skip = 4)
        if self.human_opponent or not self.headless:
            self.frame_skip = 1
        else:
            self.frame_skip = 4
            
        print(f"DuelEnv Initialized in mode: {self.mode} (Headless: {headless}, Difficulty: {difficulty}, FrameSkip: {self.frame_skip})")
        
        # Initialize Game
        self.game = Game(headless=self.headless)
        self.game.paused = False
        
        # Actions: 0: Idle, 1-4: Move, 5: Attack, 6: Ability 1, 7: Ability 2
        # 8: Summon Tank, 9: Summon Ranger, 10: Summon Healer
        self.action_space = spaces.Discrete(11)
        
        # Observation: 
        # Old: [BossX, BossY, PlayerX, PlayerY, BossHP, PlayerHP, Phase, CD1, CD2] (9)
        # New: Old(9) + WallRays(8) + EnemyRays(8) + ProjSectors(8) = 33
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(33,), dtype=np.float32)
        
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
            self.opponent_model_path = "alice_ai_v1" # Expected name
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
        self._user_exit = False # Reset exit flag
        
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
        self.boss.health = 4000
        self.boss.max_health = 4000
        
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
        
        # 6. Remove Spawners and Trapdoors (Distractors)
        # We iterate through the grid and replace them with Floor
        # This ensures the AI doesn't get distracted or teleport
        from core.registry import Registry
        floor_cell = Registry.get_cell("Floor")
        
        if floor_cell:
            for y in range(self.game.world.height):
                for x in range(self.game.world.width):
                    cell = self.game.world.get_cell(x, y)
                    if cell:
                         if cell.name == "Spawner" or cell.name == "Trapdoor":
                             self.game.world.set_cell(x, y, floor_cell)
        
        return self._get_obs(), {}

    def get_cd_norm(self, name, duration):
        if not self.boss: return 0.0
        cur = pygame.time.get_ticks()
        # Ensure boss has ability_cooldowns
        if not hasattr(self.boss, 'ability_cooldowns'): return 0.0
        last = self.boss.ability_cooldowns.get(name, 0)
        if cur - last > duration: return 0.0
        else: return (last + duration - cur) / duration

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
        # ONLY if Human is NOT playing. If Human IS playing, let them use keyboard.
        original_get_pressed = pygame.key.get_pressed
        
        if not self.human_opponent:
             pygame.key.get_pressed = lambda: defaultdict(int) # Block keys for AI
        
        try:
            # Frame Skipping: Run frame_skip frames per action
            for _ in range(self.frame_skip):
                self.game.logic.update()
        except Exception as e:
            print(f"Error during logic update: {e}")
            traceback.print_exc()
            
        finally:
            if not self.human_opponent:
                pygame.key.get_pressed = original_get_pressed
        
        # Handle Pygame Events
        # Handle Pygame Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # signal exit via info, don't hard quit
                terminated = True
                truncated = True # Force end
                
                # We need to pass this info out.
                # Since we return at the end, we'll set a local flag or inject into existing 'info' dict if we had one (we create it at return)
                # Let's handle this by checking a flag at return.
                self._user_exit = True
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._user_exit = True
                    terminated = True
            
            # Forward events if human playing
            if self.human_opponent and self.game:
                self.game.logic.handle_event(event)

        # ... (rest of function) ...
        # But wait, we need to return 'info'.
        # The logic continues... we should insert the check before return.
        
        # Let's set a class attribute or just check checks here.
        # But we need to make sure we don't return early and skip reward calc?
        # Actually, if user quits, we just want to stop.


        # 4. Calculate Rewards
        current_boss_hp = self.boss.health if self.boss else 0
        current_player_hp = self.game.player.health
        
        dmg_dealt_to_boss = self.prev_boss_hp - current_boss_hp
        dmg_dealt_to_player = self.prev_player_hp - current_player_hp
        
        # Calculate Minion Damage
        minion_dmg = 0
        if self.boss:
            minion_dmg = getattr(self.boss, 'minion_damage_dealt', 0)
        
        reward = 0
        
        if self.mode == "TRAIN_BOSS":
            # Reward Boss
            # + Damage Dealt to Player, - Damage Taken
            reward = (dmg_dealt_to_player * REWARD_DMG_DEALT_MULTIPLIER) - (dmg_dealt_to_boss * REWARD_DMG_TAKEN_MULTIPLIER)
            reward -= REWARD_STEP_PENALTY
            
            # Minion Reward
            if minion_dmg > 0:
                reward += minion_dmg * 0.5
                self.boss.minion_damage_dealt = 0 # Reset
            
            dmg_dealt = dmg_dealt_to_player
            dmg_taken = dmg_dealt_to_boss
            
            # Wall Collision Penalty (Slight)
            if self.boss:
                # Check center point or just simple bounds check
                # A robust check uses the game physics, but here we can check if the tile the boss is on is walkable.
                # Boss width is usually > 1, so we check corners?
                # Simplified: Check center tile
                bx_tile = int(self.boss.x / CELL_SIZE)
                by_tile = int(self.boss.y / CELL_SIZE)
                
                # Check neighbors if we really want to punish sticking to walls
                # Or just check if we are actually colliding with a wall (physics handles collision, so x/y won't be IN a wall usually)
                # But if physics pushed us out, we were touching it.
                # Let's use the game's get_tile logic.
                
                # Better approach: Punish being near walls? Or just actual collision?
                # User said "if he is in a wall are coliding with on".
                # Since physics prevents being "in" a wall, we punish being "blocked" or very close.
                # Let's check 4 points around the boss.
                
                colliding = False
                corners = [
                    (self.boss.x, self.boss.y),
                    (self.boss.x + self.boss.w * CELL_SIZE, self.boss.y),
                    (self.boss.x, self.boss.y + self.boss.h * CELL_SIZE),
                    (self.boss.x + self.boss.w * CELL_SIZE, self.boss.y + self.boss.h * CELL_SIZE)
                ]
                
                for cx, cy in corners:
                    tx, ty = int(cx // CELL_SIZE), int(cy // CELL_SIZE)
                    tile = self.game.world.get_cell(tx, ty)
                    if tile and not tile.walkable:
                        colliding = True
                        break
                        
                if colliding:
                    reward -= REWARD_WALL_COLLISION_PENALTY # Slight punishment per step
            
        elif self.mode == "TRAIN_PLAYER":
            dmg_dealt = dmg_dealt_to_boss
            dmg_taken = dmg_dealt_to_player
            
            reward = (dmg_dealt * REWARD_DMG_DEALT_MULTIPLIER) - (dmg_taken * REWARD_DMG_TAKEN_MULTIPLIER)
            reward -= REWARD_STEP_PENALTY
        
        # Whiff Punishment & Distance Reward
        if self.mode == "TRAIN_BOSS" and self.boss:
            # Controlling Boss
             if action == 5 and dmg_dealt <= 0:
                 reward -= REWARD_WHIFF_PENALTY
             
             dist = ((self.game.player.x - self.boss.x)**2 + (self.game.player.y - self.boss.y)**2)**0.5
             if DISTANCE_BONUS_MIN < dist < DISTANCE_BONUS_MAX:
                 reward += REWARD_DISTANCE_BONUS
                 
        elif self.mode == "TRAIN_PLAYER":
            # Controlling Player
            # Action 5 might be attack for player too?
             if action == 5 and dmg_dealt <= 0: # Assuming player dmg_dealt is to boss (dmg_dealt var is boss loss?)
                 # In TRAIN_PLAYER, we want to MAXIMIZE Boss Damage Taken.
                 # dmg_dealt = prev_boss_hp - cur_boss_hp. So positive dmg_dealt is good.
                 reward -= REWARD_WHIFF_PENALTY
             
             dist = ((self.game.player.x - self.boss.x)**2 + (self.game.player.y - self.boss.y)**2)**0.5
             if DISTANCE_BONUS_MIN < dist < DISTANCE_BONUS_MAX:
                 reward += REWARD_DISTANCE_BONUS

        if current_boss_hp <= 0:
            if self.mode == "TRAIN_BOSS": reward -= REWARD_LOSS # Boss Died (Bad)
            else: reward += REWARD_WIN # Boss Died (Good for Player)
        
        if current_player_hp <= 0:
            if self.mode == "TRAIN_BOSS": reward += REWARD_WIN # Player Died (Good for Boss)
            else: reward -= REWARD_LOSS # Player Died (Bad)         
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
        if dmg_dealt != 0 or dmg_taken != 0 or minion_dmg > 0:
            self.last_damage_step = self.step_count
            
        if self.step_count - self.last_damage_step > 500:
            terminated = True
            # Stalemate Penalty
            reward -= REWARD_STALEMATE_PENALTY
            truncated = True # Or just terminated? Truncated is better for time limit.
            
        if terminated and winner is not None:
             self.win_history.append(winner)
             
        # Scale Reward for Stability (PPO likes -1 to 1)
        reward = reward / 100.0
             
        info = {}
        if hasattr(self, '_user_exit') and self._user_exit:
            info['user_exit'] = True
             
        return self._get_obs(), reward, terminated, truncated, info

    def _get_obs(self):
        if not self.boss or not self.game.player:
            return np.zeros(33, dtype=np.float32)
            
        # 1. Determine "Self" and "Opponent" based on Mode
        if self.mode == "TRAIN_BOSS":
            me = self.boss
            opp = self.game.player
            # For Boss, normalized coordinates
            my_x = me.x / (GRID_WIDTH * CELL_SIZE)
            my_y = me.y / (GRID_HEIGHT * CELL_SIZE)
            # Opponent relative to world
            opp_x = opp.x / (GRID_WIDTH * CELL_SIZE)
            opp_y = opp.y / (GRID_HEIGHT * CELL_SIZE)
            
            my_hp = me.health / me.max_health
            opp_hp = opp.health / opp.max_health
            
            # Boss specific
            phase = me.phase / 3.0 if hasattr(me, "phase") else 0
            cd1 = self.get_cd_norm("projectile", 2000) # Example
            cd2 = self.get_cd_norm("dash", 5000)
            
        else: # TRAIN_PLAYER
            me = self.game.player
            opp = self.boss
            
            my_x = me.x / (GRID_WIDTH * CELL_SIZE)
            my_y = me.y / (GRID_HEIGHT * CELL_SIZE)
            
            opp_x = opp.x / (GRID_WIDTH * CELL_SIZE)
            opp_y = opp.y / (GRID_HEIGHT * CELL_SIZE)
            
            my_hp = me.health / me.max_health
            opp_hp = opp.health / opp.max_health
            
            phase = 0 # Player doesn't need phase? Or maybe boss phase is useful info
            if opp:
                 phase = opp.phase / 3.0 if hasattr(opp, "phase") else 0
                 
            # Player cooldowns
            cd1 = 0 # TODO: hook up player cooldowns
            cd2 = 0
            
        base_obs = [
            my_x, my_y, opp_x, opp_y, my_hp, opp_hp, phase, cd1, cd2
        ]
        
        # --- VISION SYSTEM ---
        # 8 Directions: N, NE, E, SE, S, SW, W, NW
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        max_view_dist = 500 # pixels
        
        wall_obs = []
        enemy_obs = []
        
        cx, cy = me.x + (me.w * CELL_SIZE)//2, me.y + (me.h * CELL_SIZE)//2
        
        for deg in angles:
            rad = math.radians(deg)
            # Wall Ray
            w_dist = cast_wall_ray(self.game, cx, cy, rad, max_view_dist)
            wall_obs.append(w_dist)
            
            # Entity Ray (Opponent)
            e_dist = cast_entity_ray(self.game, cx, cy, rad, max_view_dist, opp)
            enemy_obs.append(e_dist)
            
        # --- PROJECTILE SECTOR SCAN ---
        # Check 8 sectors for ANY dangerous projectile
        # Closest projectile determines the value (1.0 = VERY close)
        proj_sectors = [0.0] * 8
        
        # We need to know which projectiles are dangerous.
        # If I am Boss, Player projectiles are dangerous.
        # If I am Player, Enemy projectiles are dangerous.
        
        dangerous_projs = []
        for p in self.game.projectiles:
            if self.mode == "TRAIN_BOSS":
                if p.owner_type == "player": dangerous_projs.append(p)
            else:
                if p.owner_type == "enemy": dangerous_projs.append(p)
                
        for p in dangerous_projs:
            # Vector to projectile
            dx = p.x - cx
            dy = p.y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < max_view_dist:
                # Calculate angle
                angle = math.degrees(math.atan2(dy, dx))
                if angle < 0: angle += 360
                
                # Map to 8 sectors (0-45 -> 0, etc.)
                # Normalizing angle to index 0-7
                # We want sectors centered on 0, 45, 90...
                # Sector 0 covers 337.5 to 22.5.
                # Sector 1 covers 22.5 to 67.5.
                
                idx = int((angle + 22.5) // 45) % 8
                
                # Value: Closer = Higher
                val = 1.0 - (dist / max_view_dist)
                
                # Keep max danger for that sector
                if val > proj_sectors[idx]:
                    proj_sectors[idx] = val
                    
        # Concat all
        full_obs = np.array(base_obs + wall_obs + enemy_obs + proj_sectors, dtype=np.float32)
        
        # Sanity check shape
        if full_obs.shape[0] != 33:
             print(f"WARNING: Obs shape mismatch! Expected 33, got {full_obs.shape[0]}")
             # Pad or truncate
             full_obs = np.resize(full_obs, (33,))
             
        return full_obs

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
