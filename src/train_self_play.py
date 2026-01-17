"""
Multi-Core Optimized AI Training Script (Persistent & Dynamic)
"""

# CRITICAL: Set environment variables BEFORE any other imports
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['TORCH_NUM_THREADS'] = '1'

import sys
import glob
import numpy as np
import gc
from ai.duel_env import DuelEnv
from ai.training_utils import (
    MultiCoreCallback, 
    set_worker_cpu_affinity, 
    get_cpu_profile,
    parse_training_args,
    print_training_header
)

class MakeOptimizedEnv:
    def __init__(self, env_id, **kwargs):
        self.env_id = env_id
        self.kwargs = kwargs
        
    def __call__(self):
        from ai.duel_env import DuelEnv
        from stable_baselines3.common.monitor import Monitor
        from ai.training_utils import set_worker_cpu_affinity
        
        # Set CPU affinity for this worker
        env_kwargs = self.kwargs.copy()
        num_workers = env_kwargs.pop('_num_workers', os.cpu_count())
        set_worker_cpu_affinity(self.env_id, num_workers)
        
        env = DuelEnv(**env_kwargs)
        env = Monitor(env)
        return env

def train(iterations=15, n_envs=None, target="BOTH", use_history=True, cpu_profile='AUTO'):
    # Detect Hardware Profile
    profile = get_cpu_profile(cpu_profile, n_envs)
    if n_envs is None:
        n_envs = profile['recommended_workers']
    
    ITERATIONS = iterations
    
    # --- DYNAMIC TUNING ---
    # Adjust hyperparameters based on the hardware profile
    if "AMD" in profile['name']:
        # Ryzen 7950X Optimized Settings
        STEPS_PER_ROUND = 40000 
        PPO_KWARGS = {
            "n_steps": 2048,      # Large buffer for 16 cores
            "batch_size": 2048,   # Massive batch for AVX-512
            "learning_rate": 3e-4,
            "n_epochs": 5,        # Fast updates
            "device": "cpu",
            "verbose": 1
        }
    else:
        # Standard Settings (Safer for lower core counts)
        STEPS_PER_ROUND = 20000
        PPO_KWARGS = {
            "n_steps": 1024,
            "batch_size": 512,
            "learning_rate": 3e-4,
            "n_epochs": 10,
            "device": "cpu",
            "verbose": 1
        }

    boss_model_name = "joern_boss_ai_v1"
    player_model_name = "alice_ai_v1"
    
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize, VecFrameStack
        from sb3_contrib import RecurrentPPO
    except ImportError:
        print("❌ Error: stable_baselines3 or sb3-contrib not installed.")
        return

    print("\n" + "="*70)
    print("🚀 PERSISTENT SELF-PLAY TRAINING")
    print("="*70)
    print(f"🎯 Target: {target}")
    print(f"💻 Profile: {profile['name']}")
    print(f"🔢 Workers: {n_envs}")
    print(f"⚡ Batch Size: {PPO_KWARGS['batch_size']}")
    print("="*70 + "\n")

    if not os.path.exists("models"):
        os.makedirs("models")
        
    boss_history = []
    player_history = []
    
    if os.path.exists("models"):
        b_files = glob.glob("models/boss_gen_*.zip")
        boss_history = [b.replace(".zip", "") for b in b_files]
        p_files = glob.glob("models/alice_gen_*.zip")
        player_history = [p.replace(".zip", "") for p in p_files]

    # --- 1. INITIALIZE ENVIRONMENTS (ONCE) ---
    print("🔧 Initializing Environments (This takes a moment)...")
    
    env_boss = None
    env_player = None
    
    if target in ["BOTH", "BOSS"]:
        env_fns = [MakeOptimizedEnv(i, mode="TRAIN_BOSS", human_opponent=False, headless=True, opponent_pool=[], _num_workers=n_envs) for i in range(n_envs)]
        env_boss = SubprocVecEnv(env_fns)
        env_boss = VecFrameStack(env_boss, n_stack=4)
        env_boss = VecNormalize(env_boss, norm_obs=True, norm_reward=True, gamma=0.99)

    if target in ["BOTH", "PLAYER"]:
        env_fns = [MakeOptimizedEnv(i, mode="TRAIN_PLAYER", human_opponent=False, headless=True, opponent_pool=[], _num_workers=n_envs) for i in range(n_envs)]
        env_player = SubprocVecEnv(env_fns)
        env_player = VecFrameStack(env_player, n_stack=4)
        env_player = VecNormalize(env_player, norm_obs=True, norm_reward=True, gamma=0.99)

    # --- 2. LOAD MODELS ---
    boss_model = None
    player_model = None

    if env_boss:
        if os.path.exists(boss_model_name + ".zip"):
            print(f"📂 Loading Boss Model...")
            boss_model = RecurrentPPO.load(boss_model_name, env=env_boss, device="cpu")
        else:
            print("✨ Creating NEW Boss Model")
            boss_model = RecurrentPPO("MlpLstmPolicy", env_boss, **PPO_KWARGS)

    if env_player:
        if os.path.exists(player_model_name + ".zip"):
            print(f"📂 Loading Player Model...")
            player_model = RecurrentPPO.load(player_model_name, env=env_player, device="cpu")
        else:
            print("✨ Creating NEW Player Model")
            player_model = RecurrentPPO("MlpLstmPolicy", env_player, **PPO_KWARGS)

    # --- 3. TRAINING LOOP ---
    print("\n⚡ Training Loop Started")
    i = 1
    
    try:
        while i <= ITERATIONS:
            print(f"\n--- ROUND {i}/{ITERATIONS} ---")
            
            # === TRAIN BOSS ===
            if boss_model:
                print_training_header(i, ITERATIONS, "BOSS", n_envs)
                
                # Update opponents dynamically WITHOUT restarting env
                current_opponents = player_history if use_history else []
                env_boss.env_method("set_opponent_pool", current_opponents)
                
                callback = MultiCoreCallback(n_envs=n_envs, verbose=1)
                boss_model.learn(total_timesteps=STEPS_PER_ROUND, reset_num_timesteps=False, callback=callback)
                
                boss_model.save(boss_model_name)
                v_name = f"models/boss_gen_{i}"
                boss_model.save(v_name)
                boss_history.append(v_name)
                
                if env_boss: env_boss.save("models/vec_normalize_boss.pkl")
                print(f"✅ Boss Gen {i} Saved")

            # === TRAIN PLAYER ===
            if player_model:
                print_training_header(i, ITERATIONS, "PLAYER", n_envs)
                
                current_opponents = boss_history if use_history else []
                env_player.env_method("set_opponent_pool", current_opponents)
                
                callback = MultiCoreCallback(n_envs=n_envs, verbose=1)
                player_model.learn(total_timesteps=STEPS_PER_ROUND, reset_num_timesteps=False, callback=callback)
                
                player_model.save(player_model_name)
                v_name = f"models/alice_gen_{i}"
                player_model.save(v_name)
                player_history.append(v_name)
                
                if env_player: env_player.save("models/vec_normalize_player.pkl")
                print(f"✅ Player Gen {i} Saved")
                
            i += 1
            gc.collect()

    except KeyboardInterrupt:
        print("\n⚠️ Training Interrupted! Saving state...")
        if boss_model: boss_model.save(boss_model_name)
        if player_model: player_model.save(player_model_name)
        
    finally:
        print("Cleaning up environments...")
        if env_boss: env_boss.close()
        if env_player: env_player.close()
        print("Done.")

if __name__ == "__main__":
    args = parse_training_args()
    train(
        iterations=args.iterations,
        n_envs=args.workers,
        target=args.target,
        use_history=not args.no_history,
        cpu_profile=args.cpu
    )