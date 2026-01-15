"""
Training utilities for multi-core optimization and performance monitoring.
"""
import os
import time
import psutil
import numpy as np
from stable_baselines3.common.callbacks import BaseCallback
from typing import Dict, List


class MultiCoreCallback(BaseCallback):
    """
    Custom callback for monitoring multi-core training performance.
    Displays FPS, instance count, and CPU core assignments.
    """
    
    def __init__(self, n_envs: int, verbose: int = 1):
        super().__init__(verbose)
        self.n_envs = n_envs
        self.episode_rewards = []
        self.episode_lengths = []
        self.start_time = time.time()
        self.last_log_time = time.time()
        self.last_timestep = 0
        self.current_fps = 0
        
        # Get CPU info
        self.cpu_count = os.cpu_count()
        self.core_assignments = self._get_core_assignments()
        
    def _get_core_assignments(self) -> Dict[int, int]:
        """Generate core assignment mapping for each environment."""
        assignments = {}
        for env_id in range(self.n_envs):
            core_id = env_id % self.cpu_count
            assignments[env_id] = core_id
        return assignments
    
    def _on_training_start(self) -> None:
        """Called when training starts."""
        print("\n" + "="*70)
        print(f"🚀 MULTI-CORE TRAINING STARTED")
        print("="*70)
        print(f"📊 Total CPU Cores: {self.cpu_count}")
        print(f"🔢 Training Instances: {self.n_envs}")
        print(f"⚙️  Instances per Core: {self.n_envs / self.cpu_count:.1f}")
        print("\n📍 Core Assignment Map:")
        
        # Display core assignments in a compact format
        for env_id, core_id in self.core_assignments.items():
            if env_id % 4 == 0:
                print()
            print(f"  Instance {env_id:2d} → Core {core_id:2d}", end="  ")
        print("\n" + "="*70 + "\n")
        
    def _on_step(self) -> bool:
        """Called after each step."""
        # Calculate FPS every second
        current_time = time.time()
        elapsed = current_time - self.last_log_time
        
        if elapsed >= 1.0:  # Update every second
            timesteps_done = self.num_timesteps - self.last_timestep
            self.current_fps = timesteps_done / elapsed
            
            self.last_log_time = current_time
            self.last_timestep = self.num_timesteps
            
        return True
    
    def _on_rollout_end(self) -> None:
        """Called at the end of rollout (before training update)."""
        # Get episode info from logger if available
        if len(self.model.ep_info_buffer) > 0:
            ep_info = self.model.ep_info_buffer[-1]
            if 'r' in ep_info:
                self.episode_rewards.append(ep_info['r'])
            if 'l' in ep_info:
                self.episode_lengths.append(ep_info['l'])
    
    def _on_training_end(self) -> None:
        """Called when training ends."""
        total_time = time.time() - self.start_time
        print("\n" + "="*70)
        print(f"✅ TRAINING COMPLETED")
        print(f"⏱️  Total Time: {total_time:.1f}s")
        print(f"📈 Total Timesteps: {self.num_timesteps}")
        print(f"⚡ Average FPS: {self.num_timesteps / total_time:.0f}")
        print("="*70 + "\n")


def set_worker_cpu_affinity(worker_id: int, num_workers: int) -> int:
    """
    Set CPU affinity for the current worker process.
    
    Args:
        worker_id: ID of the current worker (0-indexed)
        num_workers: Total number of workers
        
    Returns:
        The CPU core ID this worker is assigned to
    """
    try:
        cpu_count = os.cpu_count()
        # Distribute workers evenly across cores
        core_id = worker_id % cpu_count
        
        # Set affinity for current process
        p = psutil.Process()
        p.cpu_affinity([core_id])
        
        return core_id
    except Exception as e:
        # Silently fail if affinity setting is not supported
        return -1


def get_cpu_info() -> Dict[str, int]:
    """
    Get CPU information for optimization.
    
    Returns:
        Dictionary with CPU count and recommended worker count
    """
    cpu_count = os.cpu_count()
    
    # Use all available cores for maximum parallelism
    recommended_workers = cpu_count
    
    return {
        'cpu_count': cpu_count,
        'recommended_workers': recommended_workers,
        'physical_cores': psutil.cpu_count(logical=False)
    }


def print_training_header(iteration: int, total_iterations: int, phase: str, 
                         n_envs: int, fps: float = None):

    """
    Print a formatted training header with performance info.
    
    Args:
        iteration: Current iteration number
        total_iterations: Total number of iterations
        phase: Training phase (e.g., "BOSS", "PLAYER")
        n_envs: Number of parallel environments
        fps: Current FPS (if available)
    """
    print("\n" + "="*70)
    print(f"🎯 ITERATION [{iteration}/{total_iterations}] - Training {phase}")
    print("="*70)
    print(f"🔢 Active Instances: {n_envs}")
    
    if fps is not None:
        print(f"⚡ Current FPS: {fps:.0f}")
        
    cpu_info = get_cpu_info()
    print(f"💻 CPU Cores Available: {cpu_info['cpu_count']} "
          f"(Physical: {cpu_info['physical_cores']})")
    print("="*70)


def optimize_environment_variables():
    """
    Set optimal environment variables for multi-core training.
    Must be called before importing any ML libraries.
    """
    # Prevent thread over-subscription
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['NUMEXPR_NUM_THREADS'] = '1'
    
    # PyTorch specific
    os.environ['TORCH_NUM_THREADS'] = '1'
    
    # Disable TensorFlow if it's accidentally imported
    os.environ['TF_NUM_INTEROP_THREADS'] = '1'
    os.environ['TF_NUM_INTRAOP_THREADS'] = '1'


# CPU Optimization Profiles
CPU_PROFILES = {
    'AMD_RYZEN_7950X': {
        'name': 'AMD Ryzen 9 7950X',
        'cores': 16,
        'threads': 32,
        'recommended_workers': 24,  # 75% of threads for optimal performance
        'description': '16-core/32-thread beast - using 24 workers for best performance'
    },
    'INTEL_I7_11GEN': {
        'name': 'Intel Core i7 11th Gen',
        'cores': 8,
        'threads': 16,
        'recommended_workers': 12,  # 75% of threads
        'description': '8-core/16-thread - using 12 workers for best performance'
    },
    'AUTO': {
        'name': 'Auto-Detect',
        'cores': None,  # Will be detected
        'threads': None,  # Will be detected
        'recommended_workers': None,  # Will be calculated
        'description': 'Automatically detect and optimize for your CPU'
    }
}


def get_cpu_profile(profile_name: str = 'AUTO', manual_workers: int = None) -> Dict:
    """
    Get optimized CPU configuration based on profile or auto-detection.
    
    Args:
        profile_name: CPU profile name ('AMD_RYZEN_7950X', 'INTEL_I7_11GEN', or 'AUTO')
        manual_workers: Manual override for worker count (None = use profile recommendation)
    
    Returns:
        Dictionary with CPU configuration
    """
    profile_name = profile_name.upper()
    
    # Get detected CPU info
    detected_cores = psutil.cpu_count(logical=False)
    detected_threads = os.cpu_count()
    
    if profile_name == 'AUTO' or profile_name not in CPU_PROFILES:
        # Auto-detect mode
        if manual_workers is not None:
            recommended = manual_workers
        else:
            # Use 75% of available threads for optimal performance
            recommended = max(1, int(detected_threads * 0.75))
        
        return {
            'profile': 'AUTO',
            'name': f'Auto-Detected ({detected_cores}C/{detected_threads}T)',
            'cores': detected_cores,
            'threads': detected_threads,
            'recommended_workers': recommended,
            'description': f'Auto-detected: {detected_cores} cores, {detected_threads} threads'
        }
    
    # Use predefined profile
    profile = CPU_PROFILES[profile_name].copy()
    
    # Override with manual worker count if specified
    if manual_workers is not None:
        profile['recommended_workers'] = manual_workers
        profile['description'] += f' (manual override: {manual_workers} workers)'
    
    # Add detected info for comparison
    profile['detected_cores'] = detected_cores
    profile['detected_threads'] = detected_threads
    profile['profile'] = profile_name
    
    return profile


def parse_training_args():
    """
    Parse command-line arguments for training configuration.
    
    Returns:
        Namespace with parsed arguments
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Multi-Core Optimized AI Training',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
CPU Profiles:
  AMD_RYZEN_7950X  - AMD Ryzen 9 7950X (16C/32T) - 24 workers
  INTEL_I7_11GEN   - Intel i7 11th Gen (8C/16T)  - 12 workers
  AUTO             - Auto-detect your CPU (default)

Examples:
  python src/train_self_play.py --cpu AMD_RYZEN_7950X
  python src/train_self_play.py --cpu INTEL_I7_11GEN --workers 16
  python src/train_self_play.py --workers 8 --target BOSS
        '''
    )
    
    parser.add_argument(
        '--cpu', 
        type=str, 
        default='AUTO',
        choices=['AMD_RYZEN_7950X', 'INTEL_I7_11GEN', 'AUTO'],
        help='CPU profile to use for optimization (default: AUTO)'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int, 
        default=None,
        help='Number of parallel environments (overrides CPU profile recommendation)'
    )
    
    parser.add_argument(
        '--iterations', '-i',
        type=int,
        default=15,
        help='Number of training iterations (default: 15)'
    )
    
    parser.add_argument(
        '--target', '-t',
        type=str,
        default='BOTH',
        choices=['BOTH', 'BOSS', 'PLAYER'],
        help='Training target (default: BOTH)'
    )
    
    parser.add_argument(
        '--no-history',
        action='store_true',
        help='Disable training against historical models'
    )
    
    return parser.parse_args()

