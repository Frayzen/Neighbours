import os
import pygame
import sys

# Assuming running from root, so src is in path if we run via main.
# If running directly "python src/play_vs_ai.py", we might need to adjust path if imports fail.
# But user instructions said "removing sys.path.append lines that point to src since the files are now inside src".
# This implies we run them such that src is on path or they are relative.
# "python src/play_vs_ai.py" adds src to path.
# So "from ai.duel_env" works.

from ai.duel_env import DuelEnv
from ai.brain_vis import BrainVisualizer

def run(human_opponent=True):
    mode = "TRAIN_BOSS" # Player vs Boss (TRAIN_BOSS means Agent is Boss, so Opponent is Player)
    
    try:
        from stable_baselines3 import PPO
    except ImportError:
        print("Error: stable_baselines3 not installed or not found.")
        return

    print(f"\n--- Starting Duel Mode: {mode} (Human: {human_opponent}) ---")
    
    env = DuelEnv(mode=mode, human_opponent=human_opponent)
    
    # Load Model (Boss AI)
    model = None
    model_name = "joern_boss_ai_v1"
        
    if model_name:
        if os.path.exists(model_name + ".zip"):
             print(f"Loading model: {model_name}")
             model = PPO.load(model_name)
        else:
             print(f"Model {model_name} not found. Running with random/scripted AI.")

    # Brain Visualizer (Disabled for Live View, we use Recorder + Log Reader now)
    brain = None
    # if not human_opponent:
    #    brain = BrainVisualizer(x=20, y=100, width=600, height=500)

    # Logging History
    history = [] # list of (timestamp, [obs...], action, value)
    import time
    import csv

    obs, _ = env.reset()
    running = True
    clock = pygame.time.Clock()
    
    print("Press ESC to exit Duel Mode.")
    
    game_tick = 0

    while running:
        # Determine Action
        action = 0
        value = 0.0 # Placeholder if we can't get it easily
        
        if model:
             # Model predicts action
             action, _ = model.predict(obs)
             action = int(action)
             # To get value, we'd need model.policy.predict_values(obs_tensor), skipping for now due to complexity
        else:
             action = env.action_space.sample() 
             
        # Record Data
        # Flatten obs if it's numpy
        obs_list = obs.tolist() if hasattr(obs, 'tolist') else list(obs)
        history.append({
            "timestamp": game_tick,
            "observations": obs_list,
            "action": action,
            "value": value
        })
        game_tick += 1

        # Step
        valid_action = action
        
        obs, reward, terminated, truncated, info = env.step(valid_action)
        
        env.render()
        
        # if brain:
        #     screen = pygame.display.get_surface()
        #     brain.draw(screen, model, obs, last_action=action)
        #     pygame.display.flip()
        
        # Just flip once if we aren't drawing the brain
        pygame.display.flip()

        if info.get('user_exit'):
            running = False
            
        if terminated or truncated:
            # Only reset if we are NOT exiting
            if not info.get('user_exit'):
                 obs, _ = env.reset()
            
        if not pygame.display.get_init():
             running = False
             
        clock.tick(60)
             
    env.close()

    # Save History to CSV
    if history:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        filename = os.path.join(log_dir, "ai_match_log.csv")
        print(f"Saving match log to {filename} ({len(history)} frames)...")
        
        try:
            with open(filename, "w", newline='') as f:
                writer = csv.writer(f)
                # Header: timestamp, action, value, obs_0 ... obs_32
                header = ["timestamp", "action", "value"] + [f"obs_{i}" for i in range(len(history[0]["observations"]))]
                writer.writerow(header)
                
                for row in history:
                    line = [row["timestamp"], row["action"], row["value"]] + row["observations"]
                    writer.writerow(line)
            print("Log saved successfully.")
        except Exception as e:
            print(f"Failed to save log: {e}")

if __name__ == "__main__":
    run(human_opponent=True)
