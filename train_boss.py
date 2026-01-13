import sys
import os

# Add src to path so imports within src work
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.ai.boss_env import BossFightEnv
from stable_baselines3 import PPO

def train():
    print("Initializing Environment...")
    env = BossFightEnv()
    
    print("Setting up PPO Model...")
    model = PPO("MlpPolicy", env, verbose=1)
    
    print("Starting Training (100,000 timesteps)...")
    try:
        # If we want to see the stats overlay, we might need a custom callback or just trust the environment to not crash 
        # when we call render() manually inside step() if we uncommented it.
        # But for now, headless training is standard.
        model.learn(total_timesteps=100000)
    except KeyboardInterrupt:
        print("Training interrupted manually. Saving current progress...")
    
    print("Saving Model...")
    model.save("joern_boss_ai_v1")
    print("Model saved as joern_boss_ai_v1.zip")
    
    env.close()

if __name__ == "__main__":
    train()
