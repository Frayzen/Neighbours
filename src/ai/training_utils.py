import os
import psutil
import platform
from stable_baselines3.common.callbacks import BaseCallback
import time

def get_cpu_info():
    """Detects physical vs logical core counts."""
    logical = psutil.cpu_count(logical=True)
    physical = psutil.cpu_count(logical=False)
    return physical, logical

def set_worker_cpu_affinity(worker_id, total_workers):
    """
    Advanced Pinning.
    """
    p = psutil.Process()
    physical, logical = get_cpu_info()
    
    # Simple mapping: 
    # Workers 0-15 -> Physical Cores 0-15
    # Workers 16-31 -> Logical Cores 16-31
    target_core = worker_id % logical 
        
    try:
        p.cpu_affinity([target_core])
        if hasattr(os, 'nice'): 
            os.nice(0) 
        elif platform.system() == "Windows":
            p.nice(psutil.HIGH_PRIORITY_CLASS)
    except Exception as e:
        pass # Ignore affinity errors on some systems

class MultiCoreCallback(BaseCallback):
    def __init__(self, verbose=0, n_envs=1):
        super().__init__(verbose)
        self.n_envs = n_envs
        self.start_time = time.time()
        self.last_step = 0

    def _on_step(self) -> bool:
        return True

    def _on_rollout_end(self) -> None:
        current_time = time.time()
        elapsed = current_time - self.start_time
        if elapsed > 0:
            fps = (self.num_timesteps - self.last_step) / elapsed
            self.logger.record("time/global_fps", int(fps))
        self.start_time = current_time
        self.last_step = self.num_timesteps

def get_cpu_profile(profile_name, n_envs_requested):
    physical, logical = get_cpu_info()
    
    profile = {
        "name": "Generic",
        "description": f"Detected {physical}C/{logical}T",
        "recommended_workers": physical
    }
    
    # Profil: Nur Physische Kerne (Stabil, schnell)
    if profile_name == "AMD_RYZEN_7950X":
        profile = {
            "name": "AMD_RYZEN_7950X (Physical Only)",
            "description": "Optimized for AVX throughput (16 Workers)",
            "recommended_workers": 16 
        }
    
    # Profil: Extreme SMT (Maximale Auslastung)
    elif profile_name == "AMD_RYZEN_7950X_SMT":
        # Wir nehmen Logical Threads minus 4 (für OS/Overhead)
        workers = max(16, logical - 4)
        profile = {
            "name": f"AMD_RYZEN_7950X (Extreme SMT)",
            "description": f"Using Logical Cores ({workers} Workers)",
            "recommended_workers": workers
        }
        
    return profile

def parse_training_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=1000, help="Number of ping-pong rounds")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel envs")
    parser.add_argument("--target", type=str, default="BOTH", choices=["BOTH", "BOSS", "PLAYER"])
    parser.add_argument("--no-history", action="store_true", help="Disable training against past versions")
    parser.add_argument("--cpu", type=str, default="AUTO", help="CPU Profile Hint")
    return parser.parse_args()

def print_training_header(i, iterations, target, workers):
    print(f"\n[{i}/{iterations}] ⚔️ Training {target} ({workers} Workers)...")