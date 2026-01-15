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


class MakeOptimizedEnv:
    """
    Callable class to create optimized environments.
    Necessary for multiprocessing pickling on Windows.
    """
    def __init__(self, env_id, **kwargs):
        self.env_id = env_id
        self.kwargs = kwargs
        
    def __call__(self):
        import os
        from ai.duel_env import DuelEnv
        from stable_baselines3.common.monitor import Monitor
        from ai.training_utils import set_worker_cpu_affinity
        
        # Set CPU affinity for this worker
        env_kwargs = self.kwargs.copy()
        num_workers = env_kwargs.pop('_num_workers', os.cpu_count())
        set_worker_cpu_affinity(self.env_id, num_workers)
        
        # Create the environment
        env = DuelEnv(**env_kwargs)
        env = Monitor(env)
        return env


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
        from stable_baselines3.common.monitor import Monitor
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

    print("🔧 Initializing Training Setup...")
    
    boss_model = None
    player_model = None

    # --- INITIALIZE ENVIRONMENTS ONCE ---
    # Create a single environment pool if possible, or separate if strict separation needed.
    # Given we added 'set_mode', we can use a SINGLE pool for both.
    
    env_pool = None
    
    # Initialize the pool with default settings (will be updated in loop)
    # We use BOSS mode as default initialization
    print(f"🔧 Creating Optimized Environment Pool with {n_envs} workers...")
    env_fns = [
        MakeOptimizedEnv(
            env_id=k,
            mode="TRAIN_BOSS",
            human_opponent=False,
            headless=True,
            opponent_pool=[], # Will be set dynamically
            _num_workers=n_envs
        ) for k in range(n_envs)
    ]
    
    env_pool = SubprocVecEnv(env_fns)
    env_pool = VecFrameStack(env_pool, n_stack=4)
    env_pool = VecNormalize(env_pool, norm_obs=True, norm_reward=True, gamma=0.99)
    
    try:
        # Training Loop
        i = 1
        
        while i <= ITERATIONS:
            
            # --- TRAIN BOSS ---
            if target in ["BOTH", "BOSS"]:
                print_training_header(i, ITERATIONS, "BOSS", n_envs)
                
                current_opponents = player_history if use_history else []
                
                # 1. Update Environment Mode and Opponents
                print("🔄 Configuring Environment for BOSS Training...")
                env_pool.env_method("set_mode", "TRAIN_BOSS")
                env_pool.env_method("set_opponent_pool", current_opponents)
                
                # Reset environment to apply changes and clear state
                env_pool.reset()
                
                # 2. Load/Create Boss Model
                if boss_model is None:
                    if os.path.exists(boss_model_name + ".zip"):
                        print(f"📂 Loading Boss model...")
                        boss_model = RecurrentPPO.load(boss_model_name, env=env_pool, device="cpu")
                    else:
                        print("✨ Creating NEW Boss Model")
                        boss_model = RecurrentPPO(
                            "MlpLstmPolicy", env_pool, verbose=1, 
                            batch_size=512, n_steps=1024, learning_rate=3e-4, device="cpu"
                        )
                else:
                    boss_model.set_env(env_pool)
                
                # 3. Train
                callback = MultiCoreCallback(n_envs=n_envs, verbose=1)
                print("🎮 Training BOSS...")
                boss_model.learn(total_timesteps=STEPS_PER_ROUND, reset_num_timesteps=False, callback=callback)
                
                # 4. Save
                boss_model.save(boss_model_name)
                v_name = f"models/boss_gen_{i}"
                boss_model.save(v_name)
                boss_history.append(v_name)
                
                env_pool.save("models/vec_normalize_boss.pkl")
                print(f"💾 Saved Boss Generation {i}")
                gc.collect()

            # --- TRAIN PLAYER ---
            if target in ["BOTH", "PLAYER"]:
                print_training_header(i, ITERATIONS, "PLAYER", n_envs)
                
                current_opponents = boss_history if use_history else []
                
                # 1. Update Environment Mode and Opponents
                print("� Configuring Environment for PLAYER Training...")
                env_pool.env_method("set_mode", "TRAIN_PLAYER")
                env_pool.env_method("set_opponent_pool", current_opponents)
                
                # Reset environment
                env_pool.reset()
                
                # 2. Load/Create Player Model
                if player_model is None:
                    if os.path.exists(player_model_name + ".zip"):
                        print(f"📂 Loading Player model...")
                        player_model = RecurrentPPO.load(player_model_name, env=env_pool, device="cpu")
                    else:
                        print("✨ Creating NEW Player Model")
                        player_model = RecurrentPPO(
                            "MlpLstmPolicy", env_pool, verbose=1, 
                            batch_size=512, n_steps=1024, learning_rate=3e-4, device="cpu"
                        )
                else:
                    player_model.set_env(env_pool)
                
                # 3. Train
                callback = MultiCoreCallback(n_envs=n_envs, verbose=1)
                print("🎮 Training PLAYER...")
                player_model.learn(total_timesteps=STEPS_PER_ROUND, reset_num_timesteps=False, callback=callback)
                
                # 4. Save
                player_model.save(player_model_name)
                v_name = f"models/alice_gen_{i}"
                player_model.save(v_name)
                player_history.append(v_name)
                
                env_pool.save("models/vec_normalize_player.pkl")
                print(f"💾 Saved Player Generation {i}")
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
            if env_pool: env_pool.close()
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