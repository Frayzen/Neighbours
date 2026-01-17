"""
Sample Factory Training Script (Async PPO / IMPALA Style)
Optimized for AMD Ryzen 7950X + 7900 XTX
"""
import sys
import os
import glob

# SF requires envs to be registered globally
from sample_factory.cfg.arguments import parse_full_cfg, parse_sf_args
from sample_factory.envs.env_utils import register_env
from sample_factory.train import run_rl
from sample_factory.utils.typing import ConfigTags

# Import our Env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.duel_env import DuelEnv

# Unique Name for SF
ENV_NAME = "DuelEnv_v1"

def make_duel_env(full_env_name, cfg=None, **kwargs):
    # Determine mode based on cfg or custom args
    # Defaulting to BOSS training for now, can be swapped via args logic
    mode = "TRAIN_BOSS" 
    # NOTE: To toggle modes in SF, we'd usually use different ENV_NAMEs or cfg params
    
    env = DuelEnv(
        mode=mode,
        human_opponent=False,
        headless=True,
        opponent_pool=[] # We handle pool via file system/restarts for now
    )
    return env

def register_custom_envs():
    register_env(ENV_NAME, make_duel_env)

def train_beast_mode():
    register_custom_envs()
    
    # -- CONFIGURATION FOR BEAST MODE --
    # Arguments passed as if from command line
    sys_args = [
        f"--env={ENV_NAME}",
        "--experiment=Neighbors_SF_HighThroughput",
        "--train_for_env_steps=100000000", # 100 Million Steps
        
        # WORKERS (CPU)
        "--num_workers=28",          # Use SMT (28 of 32 threads)
        "--num_envs_per_worker=1",   # 1 Env per process is usually stable for Python logic
        
        # BATCHING (GPU)
        "--batch_size=8192",         # Massive batch for 7900 XTX
        "--num_batches_per_epoch=1",
        "--num_epochs=1",            # Fast updates (Off-Policy style APPO)
        
        # ALGO
        "--algo=APPO",               # Asynchronous PPO
        "--use_rnn=True",            # Use LSTM
        "--rnn_size=256",
        "--recurrence=32",           # BPTT length
        "--gamma=0.99",
        
        # SPEED
        "--async_rl=True",           # KEY: Decouples Sampling from Learning
        "--serial_mode=False",
        "--device=gpu",              # Try GPU (requires working PyTorch ROCm)
        
        # STACKING (SF handles this natively, so DuelEnv returns 36, SF makes it 144)
        "--frame_stack=4",           
        "--normalize_input=True",    # SF handles normalization
    ]
    
    cfg = parse_sf_args(argv=sys_args)
    status = run_rl(cfg)
    return status

if __name__ == "__main__":
    train_beast_mode()