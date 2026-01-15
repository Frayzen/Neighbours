import os
import pygame
import sys
import numpy as np
import csv
from datetime import datetime
import traceback

# Imports
from ai.duel_env import DuelEnv

# Stable Baselines 3
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from stable_baselines3 import PPO

def run(human_opponent=True):
    print("\n------------------------------------------")
    print("--- DEBUG: PLAY MODE (Level Up System) ---")
    print("------------------------------------------\n")
    
    mode = "TRAIN_BOSS" 
    
    # 1. SETUP ENVIRONMENT
    def make_env():
        return DuelEnv(mode=mode, human_opponent=human_opponent, render_mode="human")
    
    # Wrap: Dummy -> FrameStack (36 -> 144)
    env = DummyVecEnv([make_env]) 
    env = VecFrameStack(env, n_stack=4) 
    
    # 2. LOAD MODEL WITH ENVIRONMENT INJECTION
    model = None
    model_name = "joern_boss_ai_v1"
        
    if model_name and os.path.exists(model_name + ".zip"):
        print(f"Loading model: {model_name}")
        try:
            from sb3_contrib import RecurrentPPO
            # Pass env=env so model adapts to the new shape if compatible
            model = RecurrentPPO.load(model_name, env=env) 
            print("Loaded as RecurrentPPO (LSTM).")
        except ImportError:
            model = PPO.load(model_name, env=env)
            print("Loaded as Standard PPO.")
        except Exception as e:
            print(f"Error loading model: {e}")
            return
            
        if model.observation_space.shape:
            print(f"Model Expects Shape: {model.observation_space.shape}")
    else:
        print(f"Model {model_name} not found. Running with random AI.")

    # 3. RESET
    obs = env.reset()
    print(f"Initial Obs Shape: {obs.shape}") 
    
    # Check for 144 (36 * 4)
    if obs.shape[-1] != 144:
        print("CRITICAL WARNING: Observation shape is NOT 144. Stack failed?")
    
    running = True
    clock = pygame.time.Clock()
    print("Press ESC to exit.")
    
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)

    history = []
    game_tick = 0

    while running:
        action = [0]
        
        if model:
            try:
                action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts)
            except Exception as e:
                print(f"\nCRITICAL CRASH IN PREDICT:")
                print(f"Input Obs Shape: {obs.shape}")
                print(traceback.format_exc()) 
                running = False
                break
        else:
             action = [env.action_space.sample()]
             
        obs, rewards, dones, infos = env.step(action)
        episode_starts = dones
        env.render()
        
        if infos:
            info = infos[0]
            inner_env = env.envs[0]
            
            history.append({
                "timestamp": game_tick,
                "obs_boss": inner_env.get_obs_for("BOSS").tolist(),
                "obs_player": inner_env.get_obs_for("PLAYER").tolist(),
                "act_boss": info.get('boss_action', 0),
                "act_player": info.get('player_action', 0)
            })
            game_tick += 1
            
            if info.get('user_exit'):
                running = False
        
        if not pygame.display.get_init():
            running = False

        clock.tick(60)
             
    env.close()

    if history:
        log_dir = "logs"
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        filename = os.path.join(log_dir, f"ai_match_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        try:
            with open(filename, "w", newline='') as f:
                writer = csv.writer(f)
                header = ["timestamp", "act_boss", "act_player"] + [f"b_obs_{i}" for i in range(36)] + [f"p_obs_{i}" for i in range(36)]
                writer.writerow(header)
                for row in history:
                    writer.writerow([row["timestamp"], row["act_boss"], row["act_player"]] + row["obs_boss"] + row["obs_player"])
            print(f"Log saved: {filename}")
        except: pass

if __name__ == "__main__":
    run(human_opponent=True)