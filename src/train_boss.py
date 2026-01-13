import os
import sys

# imports
# We are inside src/, so we can import directly from sibling modules if we run this as a module
# But standard python imports needing root to be in path might still apply if we run "python src/train_boss.py" from root?
# No, if we run from root as "python src/train_boss.py", sys.path[0] is src/.
# So "from ai.boss_env" works.

from ai.boss_env import BossFightEnv

def train():
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.env_util import make_vec_env
        from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize
    except ImportError:
        print("Error: stable_baselines3 not installed.")
        return

    print("Initializing Vector Environment...")
    N_ENVS = 8
    print(f"Starting {N_ENVS} Parallel Game Environments...")
    
    env = make_vec_env(
        BossFightEnv, 
        n_envs=N_ENVS, 
        vec_env_cls=SubprocVecEnv, 
        env_kwargs={"headless": True, "difficulty": 2}
    )
    env = VecNormalize(env, norm_obs=True, norm_reward=True, clip_obs=10.)
    
    print("Setting up PPO Model...")
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1,
        batch_size=512,
        n_steps=2048,
        learning_rate=3e-4
    )
    
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
