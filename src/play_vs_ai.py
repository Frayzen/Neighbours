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

    # Visual Loop
    obs, _ = env.reset()
    running = True
    clock = pygame.time.Clock()
    
    print("Press ESC to exit Duel Mode.")
    
    while running:
        # Determine Action
        action = 0
        if model:
             # Model predicts action for the Environment's "agent"
             # In TRAIN_BOSS mode, the agent is the BOSS.
             # So this returns Boss Action.
             action, _ = model.predict(obs)
             action = int(action)
        else:
             action = env.action_space.sample() # Random fallback if no model
             
        # Step
        valid_action = action
        
        obs, reward, terminated, truncated, info = env.step(valid_action)
        
        env.render()
        
        if terminated or truncated:
            obs, _ = env.reset()
            
        if not pygame.display.get_init():
             running = False
             
        clock.tick(60)
             
    env.close()

if __name__ == "__main__":
    run(human_opponent=True)
