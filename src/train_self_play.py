import os
import sys
from ai.duel_env import DuelEnv

def train():
    """
    Iterative Self-Play (Ping-Pong) Training Loop.
    
    1. Train Boss AI against current Player AI (or script/random if none).
    2. Save Boss AI.
    3. Train Player AI against new Boss AI.
    4. Save Player AI.
    5. Repeat.
    """
    
    # Configuration
    ITERATIONS = 5        # How many ping-pong rounds
    STEPS_PER_ROUND = 20000 # Short rounds to iterate frequently
    
    boss_model_name = "joern_boss_ai_v1"
    player_model_name = "player_ai_v1"
    
    try:
        from stable_baselines3 import PPO
    except ImportError:
        print("Error: stable_baselines3 not installed.")
        return

    print(f"\n=== Starting Iterative Self-Play (Ping-Pong) ===")
    print(f"Iterations: {ITERATIONS}")
    print(f"Steps per round: {STEPS_PER_ROUND}")

    for i in range(1, ITERATIONS + 1):
        print(f"\n--- ROUND {i}/{ITERATIONS} ---")
        
        # ---------------------------
        # PHASE 1: TRAIN BOSS
        # ---------------------------
        print(f"[{i}/{ITERATIONS}] Training BOSS (vs Player)...")
        env_boss = DuelEnv(mode="TRAIN_BOSS", human_opponent=False)
        
        # Load existing boss model or create new
        if os.path.exists(boss_model_name + ".zip"):
            print(f"Loading existing Boss model: {boss_model_name}")
            boss_model = PPO.load(boss_model_name, env=env_boss)
        else:
            print("Creating NEW Boss model")
            boss_model = PPO("MlpPolicy", env_boss, verbose=1)
            
        try:
            boss_model.learn(total_timesteps=STEPS_PER_ROUND)
            boss_model.save(boss_model_name)
            print(f"Boss Model saved: {boss_model_name}")
        except KeyboardInterrupt:
            print("Training Interrupted! Saving and exiting...")
            boss_model.save(boss_model_name)
            env_boss.close()
            return
            
        env_boss.close()
        
        # ---------------------------
        # PHASE 2: TRAIN PLAYER
        # ---------------------------
        print(f"[{i}/{ITERATIONS}] Training PLAYER (vs Boss)...")
        env_player = DuelEnv(mode="TRAIN_PLAYER", human_opponent=False)
        
        # Load existing player model or create new
        if os.path.exists(player_model_name + ".zip"):
             print(f"Loading existing Player model: {player_model_name}")
             player_model = PPO.load(player_model_name, env=env_player)
        else:
             print("Creating NEW Player model")
             player_model = PPO("MlpPolicy", env_player, verbose=1)
             
        try:
             player_model.learn(total_timesteps=STEPS_PER_ROUND)
             player_model.save(player_model_name)
             print(f"Player Model saved: {player_model_name}")
        except KeyboardInterrupt:
             print("Training Interrupted! Saving and exiting...")
             player_model.save(player_model_name)
             env_player.close()
             return
             
        env_player.close()
        
    print("\n=== Self-Play Training Complete! ===")

if __name__ == "__main__":
    train()
