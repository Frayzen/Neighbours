"""
Multi-Core Optimized AI Training Script
Optimized for maximum CPU utilization with parallel environments
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
import psutil
from ai.duel_env import DuelEnv
from ai.training_utils import (
    MultiCoreCallback, 
    set_worker_cpu_affinity, 
    get_cpu_info,
    get_cpu_profile,
    parse_training_args,
    print_training_header
)


def create_optimized_env(env_id, **env_kwargs):
    """
    Create environment with CPU affinity optimization.
    This function is called by each worker process.
    """
    def _init():
        # Set CPU affinity for this worker
        num_workers = env_kwargs.pop('_num_workers', os.cpu_count())
        core_id = set_worker_cpu_affinity(env_id, num_workers)
        
        # Create the environment
        env = DuelEnv(**env_kwargs)
        return env
    return _init


def train(iterations=15, n_envs=None, target="BOTH", use_history=True, cpu_profile='AUTO'):
    """
    Multi-Core Optimized Self-Play Training.
    
    Args:
        iterations: Number of training iterations
        n_envs: Number of parallel environments (None = use CPU profile recommendation)
        target: Training target - "BOTH", "BOSS", or "PLAYER"
        use_history: Whether to train against historical models
        cpu_profile: CPU profile to use ('AMD_RYZEN_7950X', 'INTEL_I7_11GEN', 'AUTO')
    """
    
    # Get CPU profile configuration
    profile = get_cpu_profile(cpu_profile, n_envs)
    
    # Use profile recommendation if n_envs not specified
    if n_envs is None:
        n_envs = profile['recommended_workers']
        print(f"🔍 {profile['name']}: Using {n_envs} parallel environments")
        print(f"   {profile['description']}")
    
    # Configuration
    ITERATIONS = iterations        
    STEPS_PER_ROUND = 20000 
    
    boss_model_name = "joern_boss_ai_v1"
    player_model_name = "alice_ai_v1"
    
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.env_util import make_vec_env
        from stable_baselines3.common.vec_env import SubprocVecEnv, VecNormalize, VecFrameStack, DummyVecEnv
        from sb3_contrib import RecurrentPPO
    except ImportError:
        print("❌ Error: stable_baselines3 or sb3-contrib not installed.")
        return

    print("\n" + "="*70)
    print("🚀 MULTI-CORE OPTIMIZED SELF-PLAY TRAINING")
    print("="*70)
    print(f"🎯 Target: {target}")
    print(f"🔄 Iterations: {ITERATIONS}")
    print(f"💻 CPU Profile: {profile['name']}")
    print(f"🔢 Parallel Environments: {n_envs}")
    print(f"⚙️  Detected: {profile.get('detected_cores', 'N/A')}C/{profile.get('detected_threads', 'N/A')}T")
    print(f"📦 Steps per Round: {STEPS_PER_ROUND:,}")
    print("="*70 + "\n")

    if not os.path.exists("models"):
        os.makedirs("models")
        
    boss_history = []
    player_history = []
    
    # Load existing model history
    if os.path.exists("models"):
        b_files = glob.glob("models/boss_gen_*.zip")
        boss_history = [b.replace(".zip", "") for b in b_files]
        p_files = glob.glob("models/alice_gen_*.zip")
        player_history = [p.replace(".zip", "") for p in p_files]

    print("🔧 Initializing Training Setup...")
    
    boss_model = None
    player_model = None

    # Training Loop
    i = 1
    env_boss = None
    env_player = None
    
    try:
        while i <= ITERATIONS:
            
            # --- TRAIN BOSS ---
            if target in ["BOTH", "BOSS"]:
                print_training_header(i, ITERATIONS, "BOSS", n_envs)
                
                current_opponents = player_history if use_history else []
                
                # Create training environment FIRST
                print("🔧 Creating Boss training environment...")
                env_boss = make_vec_env(
                    lambda: DuelEnv(
                        mode="TRAIN_BOSS",
                        human_opponent=False,
                        headless=True,
                        opponent_pool=current_opponents
                    ), 
                    n_envs=n_envs, 
                    vec_env_cls=SubprocVecEnv
                )
                env_boss = VecFrameStack(env_boss, n_stack=4)
                env_boss = VecNormalize(env_boss, norm_obs=True, norm_reward=True, gamma=0.99)
                
                # Load or create model WITH the actual training environment
                if boss_model is None:
                    if os.path.exists(boss_model_name + ".zip"):
                        print(f"📂 Loading Boss model with {n_envs} workers...")
                        # Load WITH the training environment to properly handle worker count
                        boss_model = RecurrentPPO.load(
                            boss_model_name, 
                            env=env_boss,
                            device="cpu"
                        )
                    else:
                        print("✨ Creating NEW Boss Model")
                        boss_model = RecurrentPPO(
                            "MlpLstmPolicy", 
                            env_boss, 
                            verbose=1, 
                            batch_size=512, 
                            n_steps=1024, 
                            learning_rate=3e-4, 
                            device="cpu"
                        )
                else:
                    # Model already exists from previous iteration, just update env
                    print(f"🔄 Updating Boss model environment to {n_envs} workers...")
                    boss_model.set_env(env_boss)
                
                # Create callback for performance monitoring
                callback = MultiCoreCallback(n_envs=n_envs, verbose=1)
                
                print("🎮 Training BOSS...")
                boss_model.learn(
                    total_timesteps=STEPS_PER_ROUND, 
                    reset_num_timesteps=False,
                    callback=callback
                )
                boss_model.save(boss_model_name)
                
                # Archive generation
                v_name = f"models/boss_gen_{i}"
                boss_model.save(v_name)
                boss_history.append(v_name)
                
                env_boss.save("models/vec_normalize_boss.pkl")
                print(f"💾 Saved Boss Generation {i}")
                
                env_boss.close()
                env_boss = None
                gc.collect()

            # --- TRAIN PLAYER ---
            if target in ["BOTH", "PLAYER"]:
                print_training_header(i, ITERATIONS, "PLAYER", n_envs)
                
                current_opponents = boss_history if use_history else []
                
                # Create training environment FIRST
                print("🔧 Creating Player training environment...")
                env_player = make_vec_env(
                    lambda: DuelEnv(
                        mode="TRAIN_PLAYER",
                        human_opponent=False,
                        headless=True,
                        opponent_pool=current_opponents
                    ), 
                    n_envs=n_envs, 
                    vec_env_cls=SubprocVecEnv
                )
                env_player = VecFrameStack(env_player, n_stack=4)
                env_player = VecNormalize(env_player, norm_obs=True, norm_reward=True, gamma=0.99)
                
                # Load or create model WITH the actual training environment
                if player_model is None:
                    if os.path.exists(player_model_name + ".zip"):
                        print(f"📂 Loading Player model with {n_envs} workers...")
                        # Load WITH the training environment to properly handle worker count
                        player_model = RecurrentPPO.load(
                            player_model_name,
                            env=env_player,
                            device="cpu"
                        )
                    else:
                        print("✨ Creating NEW Player Model")
                        player_model = RecurrentPPO(
                            "MlpLstmPolicy", 
                            env_player, 
                            verbose=1, 
                            batch_size=512, 
                            n_steps=1024, 
                            learning_rate=3e-4, 
                            device="cpu"
                        )
                else:
                    # Model already exists from previous iteration, just update env
                    print(f"🔄 Updating Player model environment to {n_envs} workers...")
                    player_model.set_env(env_player)
                
                callback = MultiCoreCallback(n_envs=n_envs, verbose=1)
                
                print("🎮 Training PLAYER...")
                player_model.learn(
                    total_timesteps=STEPS_PER_ROUND, 
                    reset_num_timesteps=False,
                    callback=callback
                )
                player_model.save(player_model_name)
                
                v_name = f"models/alice_gen_{i}"
                player_model.save(v_name)
                player_history.append(v_name)
                
                env_player.save("models/vec_normalize_player.pkl")
                print(f"💾 Saved Player Generation {i}")
                
                env_player.close()
                env_player = None
                gc.collect()
                
            i += 1

    except KeyboardInterrupt:
        print("\n⚠️  Training Interrupted! Saving models...")
        if boss_model: 
            boss_model.save(boss_model_name)
            print(f"💾 Saved {boss_model_name}")
        if player_model: 
            player_model.save(player_model_name)
            print(f"💾 Saved {player_model_name}")
        
    finally:
        try:
            if env_boss: env_boss.close()
        except:
            pass
        try:
            if env_player: env_player.close()
        except:
            pass
        print("\n✅ Training Session Closed.")


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_training_args()
    
    # Run training with parsed arguments
    train(
        iterations=args.iterations,
        n_envs=args.workers,
        target=args.target,
        use_history=not args.no_history,
        cpu_profile=args.cpu
    )