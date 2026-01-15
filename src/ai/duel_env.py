import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
import traceback
import os
import sys
import math

# Add src directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game import Game
from config.settings import CELL_SIZE, GRID_WIDTH, GRID_HEIGHT
from ai.vision import cast_wall_ray, cast_entity_ray
try:
    from stable_baselines3 import PPO
except ImportError:
    PPO = None

try:
    from sb3_contrib import RecurrentPPO
except ImportError:
    RecurrentPPO = None

from core.input_state import InputState

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
    # Metadata for Gymnasium Standards
    metadata = {"render_modes": ["human"], "render_fps": 60}

    def __init__(self, mode="TRAIN_BOSS", human_opponent=False, headless=False, difficulty=1, opponent_pool=None, render_mode=None):
        super(DuelEnv, self).__init__()
        
        self.render_mode = render_mode
        self.mode = mode 
        self.human_opponent = human_opponent
        self.headless = headless
        self.difficulty = difficulty 
        
        # Frame Skip
        if self.human_opponent or not self.headless:
            self.frame_skip = 1
        else:
            self.frame_skip = 4
            
        print(f"DuelEnv Initialized: {self.mode} (Human: {human_opponent}, Headless: {headless})")
        
        # Initialize Game
        self.game = Game(headless=self.headless)
        self.game.paused = False
        
        # Actions: 0-10
        self.action_space = spaces.Discrete(11)
        
        # Observation: 33 inputs (Raw)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(33,), dtype=np.float32)
        
        self.boss = None
        self.prev_boss_hp = 100
        self.prev_player_hp = 100
        
        # Stats
        self.episode_count = 0
        self.total_reward = 0
        self.step_count = 0
        self.win_history = [] 
        self.font = None
        
        # Load Opponent Model (Only if NOT human)
        self.opponent_model = None
        self.opponent_pool = opponent_pool if opponent_pool else []
        
        # Don't load AI opponent if Human is playing
        if not self.human_opponent:
            if not self.opponent_pool:
                path = ""
                if self.mode == "TRAIN_BOSS":
                    path = "alice_ai_v1"
                elif self.mode == "TRAIN_PLAYER":
                    path = "joern_boss_ai_v1"
                self._load_opponent(path)
        else:
            print("Human Opponent Active: Disabling internal Opponent AI.")

    def _load_opponent(self, path):
        if not path: return
        loaded = False
        if RecurrentPPO and os.path.exists(path + ".zip"):
            try:
                self.opponent_model = RecurrentPPO.load(path)
                loaded = True
            except: pass

        if not loaded and PPO and os.path.exists(path + ".zip"):
            try:
                self.opponent_model = PPO.load(path)
                loaded = True
            except Exception as e:
                print(f"Failed to load opponent {path}: {e}")
                
        if not loaded and not os.path.exists(path + ".zip"):
             print(f"Opponent file not found: {path} (using script fallback)")
             self.opponent_model = None
                
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.episode_count += 1
        self.total_reward = 0
        self.step_count = 0
        self.last_damage_step = 0 
        
        self.game.restart_game()
        
        # Cleanup Entities
        self.game.gridObjects = [obj for obj in self.game.gridObjects if obj == self.game.player]
        self.game.enemies = [] 
        self.game.world.spawn_points = [] 
        
        # Spawn Boss
        center_x_pix = (self.game.world.width * CELL_SIZE) // 2
        center_y_pix = (self.game.world.height * CELL_SIZE) // 2
        
        from entities.boss.joern import JoernBoss
        self.boss = JoernBoss(self.game, center_x_pix, center_y_pix)
        
        self.game.gridObjects.append(self.boss)
        self.game.enemies.append(self.boss) 
        
        # Position Player
        self.game.player.x = center_x_pix - 200
        self.game.player.y = center_y_pix
        
        # Stats
        self.boss.health = 4000
        self.boss.max_health = 4000
        self.game.player.health = self.game.player.max_health
        self.prev_boss_hp = self.boss.health
        self.prev_player_hp = self.game.player.health

        self._enforce_ai_control()
        
        # Remove Distractors
        from core.registry import Registry
        floor_cell = Registry.get_cell("Floor")
        if floor_cell:
            for y in range(self.game.world.height):
                for x in range(self.game.world.width):
                    cell = self.game.world.get_cell(x, y)
                    if cell and (cell.name == "Spawner" or cell.name == "Trapdoor"):
                        self.game.world.set_cell(x, y, floor_cell)
        
        # Rotate Opponent (Only if AI vs AI)
        if not self.human_opponent and self.opponent_pool:
             selected_opp = np.random.choice(self.opponent_pool)
             self._load_opponent(selected_opp)
             
        return self._get_obs(), {}

    def _enforce_ai_control(self):
        if self.mode == "TRAIN_BOSS":
            if self.boss: self.boss.ai_controlled = True
            
            # Player is AI only if NOT Human
            if not self.human_opponent: 
                self.game.player.ai_controlled = True
            else:
                self.game.player.ai_controlled = False
                
        elif self.mode == "TRAIN_PLAYER":
            self.game.player.ai_controlled = True
            if self.opponent_model and self.boss: self.boss.ai_controlled = True
            elif self.boss: self.boss.ai_controlled = False

    def get_cd_norm(self, name, duration):
        if not self.boss: return 0.0
        cur = pygame.time.get_ticks()
        if not hasattr(self.boss, 'ability_cooldowns'): return 0.0
        last = self.boss.ability_cooldowns.get(name, 0)
        if cur - last > duration: return 0.0
        else: return (last + duration - cur) / duration

    def step(self, action):
        self._enforce_ai_control()
        obs = self._get_obs()
        
        last_boss_action = 0
        last_player_action = 0
        ai_input_state = InputState()
        
        def map_action_to_input(act, inp_state):
            if act == 1: inp_state.move_y = -1
            elif act == 2: inp_state.move_y = 1
            elif act == 3: inp_state.move_x = -1
            elif act == 4: inp_state.move_x = 1
            elif act == 5: inp_state.attack = True
            elif act == 6: inp_state.dash = True
            return inp_state

        if self.mode == "TRAIN_BOSS":
             # 1. Main Agent (Boss)
             last_boss_action = int(action)
             if self.boss: self.boss.set_ai_action(last_boss_action)
             
             # 2. Opponent (Player/Alice)
             if not self.human_opponent:
                 if self.opponent_model:
                     try:
                        p_act, _ = self.opponent_model.predict(obs)
                        last_player_action = int(p_act)
                        map_action_to_input(last_player_action, ai_input_state)
                     except Exception as e:
                        # Fallback to bot if model crashes
                        print(f"Opponent AI Crash: {e}. Falling back to script.")
                        self.opponent_model = None 
                 
                 if not self.opponent_model:
                     # Scripted Fallback
                     bot_action = self._get_bot_action()
                     last_player_action = int(bot_action)
                     map_action_to_input(last_player_action, ai_input_state)
                 
        elif self.mode == "TRAIN_PLAYER":
             last_player_action = int(action)
             map_action_to_input(last_player_action, ai_input_state)
             
             if self.opponent_model:
                 try:
                     b_act, _ = self.opponent_model.predict(obs)
                     last_boss_action = int(b_act)
                     if self.boss: self.boss.set_ai_action(last_boss_action)
                 except:
                     self.opponent_model = None 

        # Execute Game Logic
        try:
            for _ in range(self.frame_skip):
                if self.human_opponent:
                     self.game.logic.update(input_state=None) 
                else:
                     self.game.logic.update(input_state=ai_input_state)
        except Exception as e:
            print(f"Error during logic update: {e}")
            traceback.print_exc()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._user_exit = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._user_exit = True
            if self.human_opponent and self.game:
                self.game.logic.handle_event(event)

        # Rewards Calculation
        current_boss_hp = self.boss.health if self.boss else 0
        current_player_hp = self.game.player.health
        dmg_dealt_to_boss = self.prev_boss_hp - current_boss_hp
        dmg_dealt_to_player = self.prev_player_hp - current_player_hp
        
        minion_dmg = getattr(self.boss, 'minion_damage_dealt', 0) if self.boss else 0
        reward = 0
        dmg_dealt = 0
        
        if self.mode == "TRAIN_BOSS":
            reward = (dmg_dealt_to_player * REWARD_DMG_DEALT_MULTIPLIER) - (dmg_dealt_to_boss * REWARD_DMG_TAKEN_MULTIPLIER)
            reward -= REWARD_STEP_PENALTY
            if minion_dmg > 0:
                reward += minion_dmg * 0.5
                self.boss.minion_damage_dealt = 0 
            dmg_dealt = dmg_dealt_to_player
            
            # Wall Collision
            if self.boss:
                colliding = False
                corners = [(self.boss.x, self.boss.y), (self.boss.x + self.boss.w * CELL_SIZE, self.boss.y)]
                for cx, cy in corners:
                    tx, ty = int(cx // CELL_SIZE), int(cy // CELL_SIZE)
                    tile = self.game.world.get_cell(tx, ty)
                    if tile and not tile.walkable:
                        colliding = True; break
                if colliding: reward -= REWARD_WALL_COLLISION_PENALTY
            
        elif self.mode == "TRAIN_PLAYER":
            dmg_dealt = dmg_dealt_to_boss
            dmg_taken = dmg_dealt_to_player
            reward = (dmg_dealt * REWARD_DMG_DEALT_MULTIPLIER) - (dmg_taken * REWARD_DMG_TAKEN_MULTIPLIER)
            reward -= REWARD_STEP_PENALTY
        
        # Whiff & Distance
        if self.mode == "TRAIN_BOSS" and self.boss:
             if action == 5 and dmg_dealt <= 0: reward -= REWARD_WHIFF_PENALTY
             dist = ((self.game.player.x - self.boss.x)**2 + (self.game.player.y - self.boss.y)**2)**0.5
             if DISTANCE_BONUS_MIN < dist < DISTANCE_BONUS_MAX: reward += REWARD_DISTANCE_BONUS
                 
        elif self.mode == "TRAIN_PLAYER":
             if action == 5 and dmg_dealt <= 0: reward -= REWARD_WHIFF_PENALTY
             dist = ((self.game.player.x - self.boss.x)**2 + (self.game.player.y - self.boss.y)**2)**0.5
             if DISTANCE_BONUS_MIN < dist < DISTANCE_BONUS_MAX: reward += REWARD_DISTANCE_BONUS

        # Near Miss
        me = self.boss if (self.mode == "TRAIN_BOSS") else self.game.player
        if me:
             mx, my = me.x + (me.w * CELL_SIZE)/2, me.y + (me.h * CELL_SIZE)/2
             for p in self.game.projectiles:
                 is_enemy = (self.mode == "TRAIN_BOSS" and p.owner_type == "player") or (self.mode == "TRAIN_PLAYER" and p.owner_type == "enemy")
                 if is_enemy:
                     dx = p.x - mx; dy = p.y - my
                     if math.sqrt(dx*dx + dy*dy) < 40: reward += 0.05

        if current_boss_hp <= 0:
            reward -= REWARD_LOSS if self.mode == "TRAIN_BOSS" else -REWARD_WIN
        if current_player_hp <= 0:
            reward += REWARD_WIN if self.mode == "TRAIN_BOSS" else -REWARD_LOSS
            
        self.total_reward += reward
        self.step_count += 1
        self.prev_boss_hp = current_boss_hp
        self.prev_player_hp = current_player_hp
        
        terminated = False
        truncated = False
        
        if current_boss_hp <= 0 or current_player_hp <= 0:
            terminated = True
            winner = 1 if (self.mode == "TRAIN_BOSS" and current_player_hp <= 0) or (self.mode == "TRAIN_PLAYER" and current_boss_hp <= 0) else 0
            self.win_history.append(winner)
            
        if dmg_dealt != 0 or minion_dmg > 0:
            self.last_damage_step = self.step_count
        if self.step_count - self.last_damage_step > 500:
            terminated = True; truncated = True; reward -= REWARD_STALEMATE_PENALTY
            
        reward = reward / 100.0
             
        info = {}
        if hasattr(self, '_user_exit') and self._user_exit: info['user_exit'] = True
        info['boss_action'] = last_boss_action
        info['player_action'] = last_player_action
             
        return self._get_obs(), reward, terminated, truncated, info

    def get_obs_for(self, perspective="BOSS"):
        return self._get_obs(perspective)

    def _get_obs(self, perspective=None):
        if not self.boss or not self.game.player: return np.zeros(33, dtype=np.float32)
        target_mode = self.mode
        if perspective == "BOSS": target_mode = "TRAIN_BOSS"
        elif perspective == "PLAYER": target_mode = "TRAIN_PLAYER"
            
        if target_mode == "TRAIN_BOSS":
            me, opp = self.boss, self.game.player
            phase = me.phase / 3.0 if hasattr(me, "phase") else 0
            cd1 = self.get_cd_norm("projectile", 2000)
            cd2 = self.get_cd_norm("dash", 5000)
        else:
            me, opp = self.game.player, self.boss
            phase = opp.phase / 3.0 if (opp and hasattr(opp, "phase")) else 0
            cd1, cd2 = 0, 0
            
        my_x, my_y = me.x / (GRID_WIDTH * CELL_SIZE), me.y / (GRID_HEIGHT * CELL_SIZE)
        opp_x, opp_y = opp.x / (GRID_WIDTH * CELL_SIZE), opp.y / (GRID_HEIGHT * CELL_SIZE)
        base_obs = [my_x, my_y, opp_x, opp_y, me.health/me.max_health, opp.health/opp.max_health, phase, cd1, cd2]
        
        # Rays
        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        max_dist = 300
        cx, cy = me.x + (me.w*CELL_SIZE)//2, me.y + (me.h*CELL_SIZE)//2
        
        wall_obs = [cast_wall_ray(self.game, cx, cy, math.radians(a), max_dist) for a in angles]
        enemy_obs = [cast_entity_ray(self.game, cx, cy, math.radians(a), max_dist, opp) for a in angles]
            
        # Projectiles
        proj_sectors = [0.0] * 8
        dangerous = [p for p in self.game.projectiles if 
                     (target_mode == "TRAIN_BOSS" and p.owner_type == "player") or 
                     (target_mode == "TRAIN_PLAYER" and p.owner_type == "enemy")]
                     
        for p in dangerous:
            dx, dy = p.x - cx, p.y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < max_dist:
                angle = math.degrees(math.atan2(dy, dx))
                if angle < 0: angle += 360
                idx = int((angle + 22.5) // 45) % 8
                val = 1.0 - (dist / max_dist)
                if val > proj_sectors[idx]: proj_sectors[idx] = val
                    
        full_obs = np.array(base_obs + wall_obs + enemy_obs + proj_sectors, dtype=np.float32)
        if full_obs.shape[0] != 33: full_obs = np.resize(full_obs, (33,))
        return full_obs

    def render(self):
        if not getattr(self.game, 'screen', None):
             pygame.display.set_mode((self.game.world.width*CELL_SIZE, self.game.world.height*CELL_SIZE))
             from core.renderer import GameRenderer
             self.game.renderer = GameRenderer(self.game)

        self.game.camera.update(self.game.player)
        self.game.renderer.draw(self.game.camera)
        self._render_stats_overlay()
        self._render_graph()
        pygame.display.flip()

    def _render_stats_overlay(self):
        if not self.font: self.font = pygame.font.SysFont("Arial", 16)
        screen = pygame.display.get_surface()
        info = [
            f"Mode: {self.mode}",
            f"Episode: {self.episode_count}",
            f"Win Rate: {np.mean(self.win_history[-50:]):.2f}" if self.win_history else "N/A",
            f"Boss HP: {self.boss.health:.0f}",
            f"Player HP: {self.game.player.health:.0f}"
        ]
        y = 10
        for line in info:
             screen.blit(self.font.render(line, True, (255, 255, 255)), (10, y))
             y += 20
             
    def _render_graph(self):
        if len(self.win_history) < 2: return
        screen = pygame.display.get_surface()
        w, h = screen.get_size()
        graph_w, graph_h = 200, 100
        x_base, y_base = w - graph_w - 10, h - graph_h - 10
        
        # --- FIX: Safer Transparent Rect for Compatibility ---
        s = pygame.Surface((graph_w, graph_h)) # No SRCALPHA in constructor
        s.set_alpha(150) # Set overall alpha
        s.fill((0, 0, 0)) # Fill with solid black
        screen.blit(s, (x_base, y_base))
        
        pygame.draw.rect(screen, (255, 255, 255), (x_base, y_base, graph_w, graph_h), 1)
        
        vals = []
        window = 10
        for i in range(len(self.win_history)):
             start = max(0, i - window)
             subset = self.win_history[start:i+1]
             vals.append(sum(subset) / len(subset))
             
        display_vals = vals[-100:]
        step_x = graph_w / max(1, len(display_vals) - 1)
        points = []
        for i, val in enumerate(display_vals):
            px = x_base + i * step_x
            py = y_base + graph_h - (val * graph_h)
            points.append((px, py))
        if len(points) > 1: pygame.draw.lines(screen, (0, 255, 0), False, points, 2)

    def _get_bot_action(self):
        if not self.boss: return 0
        px, py = self.game.player.x, self.game.player.y
        bx, by = self.boss.x, self.boss.y
        dist_sq = (px - bx)**2 + (py - by)**2
        
        if np.random.rand() < 0.2: return 5 # Attack
        
        dx, dy = 0, 0
        if dist_sq < 200**2: # Run away
            dx = -1 if px < bx else 1
            dy = -1 if py < by else 1
        else: # Chase
            dx = 1 if px < bx else -1
            dy = 1 if py < by else -1
            
        if dy < 0: return 1
        if dy > 0: return 2
        if dx < 0: return 3
        if dx > 0: return 4
        return 0