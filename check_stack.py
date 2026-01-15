
import gymnasium as gym
import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from gymnasium import spaces

class SimpleEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(36,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
    def reset(self, seed=None):
        return np.zeros(36, dtype=np.float32), {}
    def step(self, action):
        return np.zeros(36, dtype=np.float32), 0.0, False, False, {}

def check_shape():
    env = DummyVecEnv([lambda: SimpleEnv()])
    env = VecFrameStack(env, n_stack=4)
    print(f"Original Shape: (36,)")
    print(f"Stacked Space Shape: {env.observation_space.shape}")
    obs = env.reset()
    print(f"Stacked Observation Shape: {obs.shape}")

if __name__ == "__main__":
    check_shape()
