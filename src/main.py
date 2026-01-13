import random
import sys
import os
import pygame

# Set random seed
random.seed(39)

# Fix Path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports
from core.game import gameInstance

def run_duel_mode(mode="TRAIN_BOSS", human_opponent=False, visual=True, train_steps=0):
    try:
        from stable_baselines3 import PPO
    except ImportError:
        print("Error: stable_baselines3 not installed or not found.")
        return

    from ai.duel_env import DuelEnv

    print(f"\n--- Starting Duel Mode: {mode} (Human: {human_opponent}) ---")
    
    env = DuelEnv(mode=mode, human_opponent=human_opponent)
    
    # Load Model (if AI controlled)
    model = None
    model_name = ""
    if mode == "TRAIN_BOSS":
        model_name = "joern_boss_ai_v1"
    elif mode == "TRAIN_PLAYER":
        model_name = "player_ai_v1"
        
    if model_name:
        if os.path.exists(model_name + ".zip"):
             print(f"Loading model: {model_name}")
             model = PPO.load(model_name)
        else:
             print(f"Model {model_name} not found. Running with random/scripted AI.")

    if train_steps > 0:
        print(f"Training for {train_steps} steps...")
        # Create new model if not exists
        if not model:
            print("Creating new PPO model...")
            model = PPO("MlpPolicy", env, verbose=1)
            
        try:
            model.learn(total_timesteps=train_steps)
            model.save(model_name)
            print(f"Model saved as {model_name}")
        except KeyboardInterrupt:
            print("Training interrupted.")
        
        env.close()
        return

    # Visual Loop
    obs, _ = env.reset()
    running = True
    clock = pygame.time.Clock()
    
    print("Press ESC to exit Duel Mode.")
    
    while running:
        # Determine Action
        action = 0
        if model:
             action, _ = model.predict(obs)
             action = int(action)
        else:
             action = env.action_space.sample() # Random fallback if no model
             
        # Step
        valid_action = action
        # If Player is AI in TRAIN_PLAYER mode, action is for Player.
        # If Boss is AI in TRAIN_BOSS mode, action is for Boss.
        
        obs, reward, terminated, truncated, info = env.step(valid_action)
        
        env.render()
        
        if terminated or truncated:
            obs, _ = env.reset()
            
        # Check for quit manually since env swallows events
        # (Though we patched env to swallow events, we can check basic escape here if env allows)
        # Actually our env swallows everything. But it handles QUIT. 
        # Check if window is closed?
        if not pygame.display.get_init():
             running = False
             
        # Optional: Limit FPS if visual
        if visual:
             clock.tick(60)
             
    env.close()

def run_training_mode():
    print("\n--- Training Mode ---")
    # For simplicity, we just train the Boss AI as per train_boss.py logic
    # But integrated here.
    try:
        run_duel_mode(mode="TRAIN_BOSS", human_opponent=False, visual=False, train_steps=100000)
    except Exception as e:
        print(f"Training failed: {e}")


def main_menu():
    while True:
        print("\n=== NEIGHBOURS GAME LAUNCHER ===")
        print("1. Play Game (Normal)")
        print("2. Challenge Boss (Player vs AI Boss)")
        print("3. Watch Duel (AI vs AI)")
        print("4. Train Boss AI")
        print("q. Quit")
        
        choice = input("\nSelect Option: ").strip().lower()
        
        if choice == '1':
            gameInstance.run()
        elif choice == '2':
            run_duel_mode(mode="TRAIN_BOSS", human_opponent=True)
        elif choice == '3':
            run_duel_mode(mode="TRAIN_BOSS", human_opponent=False) # AI vs AI (Boss AI vs Scripted Player or Player AI if loaded)
            # Ensure DuelEnv puts Player on AI control if human_opponent=False.
        elif choice == '4':
            run_training_mode()
        elif choice == 'q':
            print("Goodbye!")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main_menu()
