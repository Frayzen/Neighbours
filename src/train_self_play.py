import os
import sys
from ai.duel_env import DuelEnv

def train(iterations=15, n_envs=8, target="BOTH"):
    """
    Iterative Self-Play (Ping-Pong) Training Loop.
    
    Args:
        iterations (int): How many ping-pong rounds.
        n_envs (int): Number of parallel environments.
        target (str): "BOTH", "BOSS", or "PLAYER"
    """
    
    # Configuration
    ITERATIONS = iterations        
    STEPS_PER_ROUND = 20000 
    
    boss_model_name = "joern_boss_ai_v1"
    player_model_name = "alice_ai_v1"
    
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.env_util import make_vec_env
        from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize
    except ImportError:
        print("Error: stable_baselines3 not installed.")
        return

    print(f"\n=== Starting Iterative Self-Play (Ping-Pong) ===")
    print(f"Target: {target}")
    print(f"Iterations: {'Infinite' if ITERATIONS == float('inf') else ITERATIONS}")
    print(f"Steps per round: {STEPS_PER_ROUND}")

    N_ENVS = n_envs
    
    i = 1
    while i <= ITERATIONS:
        print(f"\n--- ROUND {i}/{'∞' if ITERATIONS == float('inf') else ITERATIONS} ---")
        
        # ---------------------------
        # PHASE 1: TRAIN BOSS
        # ---------------------------
        if target in ["BOTH", "BOSS"]:
            print(f"[{i}/{'∞' if ITERATIONS == float('inf') else ITERATIONS}] Training BOSS (vs Alice) | Parallel Games: {N_ENVS}")
            # env_boss = DuelEnv(mode="TRAIN_BOSS", human_opponent=False, headless=True)
            env_boss = make_vec_env(
                DuelEnv, 
                n_envs=N_ENVS, 
                vec_env_cls=SubprocVecEnv, 
                env_kwargs={"mode": "TRAIN_BOSS", "human_opponent": False, "headless": True}
            )
            env_boss = VecNormalize(env_boss, norm_obs=True, norm_reward=True, gamma=0.99)
            
            # Load existing boss model or create new
            if os.path.exists(boss_model_name + ".zip"):
                print(f"Loading existing Boss model: {boss_model_name}")
                boss_model = PPO.load(boss_model_name, env=env_boss, device="cpu")
            else:
                print("Creating NEW Boss model")
                boss_model = PPO(
                    "MlpPolicy", 
                    env_boss, 
                    verbose=1,
                    batch_size=2048,
                    n_steps=2048,
                    learning_rate=3e-4,
                    device="cpu",
                    policy_kwargs=dict(net_arch=[256, 256])
                )
                
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
        if target in ["BOTH", "PLAYER"]:
            print(f"[{i}/{'∞' if ITERATIONS == float('inf') else ITERATIONS}] Training ALICE (vs Boss) | Parallel Games: {N_ENVS}")
            # env_player = DuelEnv(mode="TRAIN_PLAYER", human_opponent=False, headless=True)
            env_player = make_vec_env(
                DuelEnv, 
                n_envs=N_ENVS, 
                vec_env_cls=SubprocVecEnv, 
                env_kwargs={"mode": "TRAIN_PLAYER", "human_opponent": False, "headless": True}
            )
            env_player = VecNormalize(env_player, norm_obs=True, norm_reward=True, gamma=0.99)
            
            # Load existing player model or create new
            if os.path.exists(player_model_name + ".zip"):
                 print(f"Loading existing Alice model: {player_model_name}")
                 player_model = PPO.load(player_model_name, env=env_player, device="cpu")
            else:
                 print("Creating NEW Alice model")
                 player_model = PPO(
                    "MlpPolicy", 
                    env_player, 
                    verbose=1,
                    batch_size=2048,
                    n_steps=2048,
                    learning_rate=3e-4,
                    device="cpu",
                    policy_kwargs=dict(net_arch=[256, 256])
                 )
                 
            try:
                 player_model.learn(total_timesteps=STEPS_PER_ROUND)
                 player_model.save(player_model_name)
                 print(f"Alice Model saved: {player_model_name}")
            except KeyboardInterrupt:
                 print("Training Interrupted! Saving and exiting...")
                 player_model.save(player_model_name)
                 env_player.close()
                 return
                 
            env_player.close()
            
        i += 1
        
    print("\n=== Self-Play Training Complete! ===")

if __name__ == "__main__":
    train()
