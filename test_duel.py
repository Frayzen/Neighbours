import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.ai.duel_env import DuelEnv
import pygame

def test():
    print("Testing TRAIN_BOSS mode...")
    env = DuelEnv(mode="TRAIN_BOSS")
    obs, _ = env.reset()
    print("Reset successful. Obs shape:", obs.shape)
    
    for i in range(10):
        action = env.action_space.sample()
        obs, reward, term, trunc, info = env.step(action)
        if i % 5 == 0:
            env.render()
            
    print("TRAIN_BOSS steps done.")
    env.close()

    print("Testing TRAIN_PLAYER mode...")
    env = DuelEnv(mode="TRAIN_PLAYER")
    env.reset()
    for i in range(10):
        action = env.action_space.sample()
        env.step(action)
        if i % 5 == 0:
            env.render()
    print("TRAIN_PLAYER steps done.")
    env.close()
    
    print("DuelEnv Test Passed.")

if __name__ == "__main__":
    test()
