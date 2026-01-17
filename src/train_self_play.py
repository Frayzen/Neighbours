"""
Multi-Core Optimized AI Training Script (Ryzen 7950X Edition)
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
    STEPS_PER_ROUND = 40000 # Increased: We process faster, so we gather more data
    
    boss_model_name = "joern_boss_ai_v1"
    player_model_name = "alice_ai_v1"
    
    try:
        from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize, VecFrameStack
        from sb3_contrib import RecurrentPPO
    except ImportError:
        print("❌ Error: stable_baselines3 not installed.")
        return

    print(f"\n🚀 RYZEN OPTIMIZED TRAINING | Workers: {n_envs} | Profile: {profile['name']}")

    if not os.path.exists("models"): os.makedirs("models")
    
    # Load History
    boss_history = [f.replace(".zip", "") for f in glob.glob("models/boss_gen_*.zip")]
    player_history = [f.replace(".zip", "") for f in glob.glob("models/alice_gen_*.zip")]

    # --- 1. INITIALIZE ENVIRONMENTS ---
    print("🔧 Spawning persistent environments...")
    
    env_boss = None
    env_player = None
    
    # Boss Envs
    if target in ["BOTH", "BOSS"]:
        env_fns = [MakeOptimizedEnv(i, mode="TRAIN_BOSS", human_opponent=False, headless=True, opponent_pool=[], _num_workers=n_envs) for i in range(n_envs)]
        env_boss = SubprocVecEnv(env_fns)
        env_boss = VecFrameStack(env_boss, n_stack=4)
        env_boss = VecNormalize(env_boss, norm_obs=True, norm_reward=True, gamma=0.99)

    # Player Envs
    if target in ["BOTH", "PLAYER"]:
        env_fns = [MakeOptimizedEnv(i, mode="TRAIN_PLAYER", human_opponent=False, headless=True, opponent_pool=[], _num_workers=n_envs) for i in range(n_envs)]
        env_player = SubprocVecEnv(env_fns)
        env_player = VecFrameStack(env_player, n_stack=4)
        env_player = VecNormalize(env_player, norm_obs=True, norm_reward=True, gamma=0.99)

    # --- 2. HYPERPARAMETERS (TUNED FOR 7950X) ---
    # Massive batches to keep 16 cores fed
    ppo_kwargs = {
        "verbose": 1,
        "n_steps": 2048,      # Buffer size per env (Total = 2048 * 16 = 32k)
        "batch_size": 2048,   # Batch size for update
        "learning_rate": 3e-4,
        "n_epochs": 5,        # Faster updates
        "device": "cpu"
    }

    # Load/Create Models
    boss_model = None
    player_model = None

    if env_boss:
        if os.path.exists(boss_model_name + ".zip"):
            print(f"📂 Loading Boss...")
            boss_model = RecurrentPPO.load(boss_model_name, env=env_boss, device="cpu")
        else:
            print("✨ Creating Boss...")
            boss_model = RecurrentPPO("MlpLstmPolicy", env_boss, **ppo_kwargs)

    if env_player:
        if os.path.exists(player_model_name + ".zip"):
            print(f"📂 Loading Player...")
            player_model = RecurrentPPO.load(player_model_name, env=env_player, device="cpu")
        else:
            print("✨ Creating Player...")
            player_model = RecurrentPPO("MlpLstmPolicy", env_player, **ppo_kwargs)

    # --- 3. TRAINING LOOP ---
    i = 1
    try:
        while i <= ITERATIONS:
            # BOSS ROUND
            if boss_model:
                print_training_header(i, ITERATIONS, "BOSS", n_envs)
                current_opps = player_history if use_history else []
                env_boss.env_method("set_opponent_pool", current_opps)
                
                boss_model.learn(total_timesteps=STEPS_PER_ROUND, reset_num_timesteps=False, callback=MultiCoreCallback(n_envs=n_envs))
                
                boss_model.save(boss_model_name)
                v_name = f"models/boss_gen_{i}"
                boss_model.save(v_name)
                boss_history.append(v_name)
                if env_boss: env_boss.save("models/vec_normalize_boss.pkl")

            # PLAYER ROUND
            if player_model:
                print_training_header(i, ITERATIONS, "PLAYER", n_envs)
                current_opps = boss_history if use_history else []
                env_player.env_method("set_opponent_pool", current_opps)
                
                player_model.learn(total_timesteps=STEPS_PER_ROUND, reset_num_timesteps=False, callback=MultiCoreCallback(n_envs=n_envs))
                
                player_model.save(player_model_name)
                v_name = f"models/alice_gen_{i}"
                player_model.save(v_name)
                player_history.append(v_name)
                if env_player: env_player.save("models/vec_normalize_player.pkl")
                
            i += 1
            gc.collect()

    except KeyboardInterrupt:
        print("\n⚠️ Training Interrupted! Saving...")
        if boss_model: boss_model.save(boss_model_name)
        if player_model: player_model.save(player_model_name)
        
    finally:
        if env_boss: env_boss.close()
        if env_player: env_player.close()

if __name__ == "__main__":
    args = parse_training_args()
    train(args.iterations, args.workers, args.target, not args.no_history, args.cpu)