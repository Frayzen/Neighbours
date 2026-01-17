"""
Multi-Core Optimized AI Training Script (Single Shared Pool Edition)
"""

# 1. CRITICAL: Env Vars for AMD Performance
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

# Wrapper class for Windows Multiprocessing
class MakeOptimizedEnv:
    def __init__(self, env_id, **kwargs):
        self.env_id = env_id
        self.kwargs = kwargs
    
    def __call__(self):
        from ai.duel_env import DuelEnv
        from stable_baselines3.common.monitor import Monitor
        from ai.training_utils import set_worker_cpu_affinity
        
        # Pin this worker to a specific core
        num_workers = self.kwargs.pop('_num_workers', 16)
        set_worker_cpu_affinity(self.env_id, num_workers)
        
        env = DuelEnv(**self.kwargs)
        env = Monitor(env)
        return env

def train(iterations=15, n_envs=None, target="BOTH", use_history=True, cpu_profile='AUTO'):
    # Detect Hardware Profile
    profile = get_cpu_profile(cpu_profile, n_envs)
    if n_envs is None:
        n_envs = profile['recommended_workers']
    
    ITERATIONS = iterations
    
    # --- DYNAMIC TUNING ---
    if "AMD" in profile['name']:
        # Ryzen 7950X Optimized Settings
        STEPS_PER_ROUND = 40000 
        PPO_KWARGS = {
            "n_steps": 2048,      # Large buffer for 16 cores (Total 32k steps)
            "batch_size": 2048,   # Massive batch for AVX-512
            "learning_rate": 3e-4,
            "n_epochs": 4,        # REDUCED: Faster "Study" phase (Less downtime)
            "device": "cpu",
            "verbose": 1
        }
    else:
        # Standard Settings
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
        from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize, VecFrameStack
        from sb3_contrib import RecurrentPPO
    except ImportError:
        print("❌ Error: stable_baselines3 not installed.")
        return

    print(f"\n🚀 RYZEN SHARED POOL TRAINING | Workers: {n_envs}")
    print(f"⚙️  Batch Size: {PPO_KWARGS['batch_size']} | Epochs: {PPO_KWARGS['n_epochs']}")

    if not os.path.exists("models"): os.makedirs("models")
    
    boss_history = [f.replace(".zip", "") for f in glob.glob("models/boss_gen_*.zip")]
    player_history = [f.replace(".zip", "") for f in glob.glob("models/alice_gen_*.zip")]

    # --- 1. INITIALIZE SHARED POOL (ONCE) ---
    print("🔧 Spawning 16 Persistent Workers (Shared)...")
    
    # We initialize in BOSS mode, but will toggle dynamically
    env_fns = [MakeOptimizedEnv(i, mode="TRAIN_BOSS", human_opponent=False, headless=True, opponent_pool=[], _num_workers=n_envs) for i in range(n_envs)]
    
    shared_env = SubprocVecEnv(env_fns)
    shared_env = VecFrameStack(shared_env, n_stack=4)
    # Shared Normalization (Both agents contribute to world stats - typically beneficial)
    shared_env = VecNormalize(shared_env, norm_obs=True, norm_reward=True, gamma=0.99)

    # --- 2. LOAD MODELS ---
    boss_model = None
    player_model = None

    # Load Boss attached to Shared Env
    if os.path.exists(boss_model_name + ".zip"):
        print(f"📂 Loading Boss...")
        boss_model = RecurrentPPO.load(boss_model_name, env=shared_env, device="cpu")
    else:
        print("✨ Creating Boss...")
        boss_model = RecurrentPPO("MlpLstmPolicy", shared_env, **PPO_KWARGS)

    # Load Player attached to Shared Env
    if os.path.exists(player_model_name + ".zip"):
        print(f"📂 Loading Player...")
        player_model = RecurrentPPO.load(player_model_name, env=shared_env, device="cpu")
    else:
        print("✨ Creating Player...")
        player_model = RecurrentPPO("MlpLstmPolicy", shared_env, **PPO_KWARGS)

    # --- 3. TRAINING LOOP ---
    print("\n⚡ Training Loop Started")
    i = 1
    
    try:
        while i <= ITERATIONS:
            
            # === TRAIN BOSS ===
            if target in ["BOTH", "BOSS"]:
                print_training_header(i, ITERATIONS, "BOSS", n_envs)
                
                # 1. Configure Env for Boss
                # We use env_method to tell the workers to switch modes internally
                shared_env.env_method("set_mode", "TRAIN_BOSS")
                
                # 2. Update Opponents
                current_opps = player_history if use_history else []
                shared_env.env_method("set_opponent_pool", current_opps)
                
                # 3. Train (Game Reset happens automatically inside learn)
                # We use reset_num_timesteps=False to keep logging consistent
                boss_model.learn(total_timesteps=STEPS_PER_ROUND, reset_num_timesteps=False, callback=MultiCoreCallback(n_envs=n_envs))
                
                # 4. Save
                boss_model.save(boss_model_name)
                v_name = f"models/boss_gen_{i}"
                boss_model.save(v_name)
                boss_history.append(v_name)
                shared_env.save("models/vec_normalize_shared.pkl") # Save stats

            # === TRAIN PLAYER ===
            if target in ["BOTH", "PLAYER"]:
                print_training_header(i, ITERATIONS, "PLAYER", n_envs)
                
                # 1. Configure Env for Player
                shared_env.env_method("set_mode", "TRAIN_PLAYER")
                
                # 2. Update Opponents
                current_opps = boss_history if use_history else []
                shared_env.env_method("set_opponent_pool", current_opps)
                
                # 3. Train
                player_model.learn(total_timesteps=STEPS_PER_ROUND, reset_num_timesteps=False, callback=MultiCoreCallback(n_envs=n_envs))
                
                # 4. Save
                player_model.save(player_model_name)
                v_name = f"models/alice_gen_{i}"
                player_model.save(v_name)
                player_history.append(v_name)
                shared_env.save("models/vec_normalize_shared.pkl")
                
            i += 1
            
            # Less Aggressive GC (Prevents stutters)
            if i % 10 == 0:
                gc.collect()

    except KeyboardInterrupt:
        print("\n⚠️ Training Interrupted! Saving state...")
        if boss_model: boss_model.save(boss_model_name)
        if player_model: player_model.save(player_model_name)
        
    finally:
        print("Cleaning up environments...")
        shared_env.close()
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