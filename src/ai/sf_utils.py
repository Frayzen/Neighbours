import torch
import numpy as np
import os
from sample_factory.algo.utils.shared_buffers import buffer_for_observation
from sample_factory.model.actor_critic import create_actor_critic
from sample_factory.utils.attr_dict import AttrDict
from gymnasium import spaces

class SFModelWrapper:
    """
    Wraps a Sample Factory model to look like a Stable-Baselines3 model.
    Allows DuelEnv to use SF models as opponents seamlessly.
    """
    def __init__(self, cfg, obs_space, action_space, checkpoint_path, device='cpu'):
        self.device = torch.device(device)
        self.cfg = cfg
        
        # Create Model Architecture
        self.actor_critic = create_actor_critic(cfg, obs_space, action_space)
        self.actor_critic.to(self.device)
        self.actor_critic.eval() # Inference Mode
        
        # Load Weights
        print(f"⚡ Loading SF Checkpoint: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.actor_critic.load_state_dict(checkpoint['model'])
        
        self.rnn_states = None

    def predict(self, obs, state=None, episode_start=None, deterministic=True):
        """
        Mimics SB3's predict method.
        obs: numpy array (144,) or (1, 144)
        """
        with torch.no_grad():
            # 1. Prepare Input
            if isinstance(obs, np.ndarray):
                obs_torch = torch.from_numpy(obs).float().to(self.device)
            else:
                obs_torch = obs.to(self.device)
                
            # Add batch dim if missing
            if obs_torch.ndim == 1:
                obs_torch = obs_torch.unsqueeze(0)
            
            # 2. Prepare RNN State
            if state is None or (episode_start is not None and episode_start[0]):
                # Initialize hidden states (Core for LSTM/GRU)
                # SF uses packed RNN states usually
                rnn_size = self.cfg.rnn_size
                num_layers = self.cfg.rnn_num_layers
                # Shape depends on architecture, simplified default here:
                state = torch.zeros((obs_torch.shape[0], rnn_size * num_layers), device=self.device)

            # 3. Forward Pass
            # SF models expect a dict of observations
            normalized_obs = self._normalize(obs_torch)
            input_dict = {'obs': normalized_obs}
            
            policy_outputs = self.actor_critic(input_dict, state, with_action_distribution=False)
            
            # 4. Extract Action
            actions = policy_outputs['actions'].cpu().numpy()
            new_rnn_state = policy_outputs['rnn_states']
            
            # Return scalar action if single env
            action = actions[0].item()
            
            return action, new_rnn_state

    def _normalize(self, obs):
        # Placeholder: If you used normalization during training, apply it here.
        # Ideally, use raw obs if the model has a Normalization Layer.
        return obs

def load_sf_model(path, observation_space, action_space):
    """
    Factory function to load an SF model from disk.
    Expects a folder containing 'config.json' and 'checkpoint.pth' 
    OR a direct path to a .pth file (assuming config is nearby).
    """
    import json
    
    # Path handling
    if path.endswith(".pth"):
        checkpoint_path = path
        model_dir = os.path.dirname(path)
    else:
        # It's a directory, find the latest checkpoint
        model_dir = path
        checkpoint_path = os.path.join(path, "checkpoint_best.pth") # Default fallback
        if not os.path.exists(checkpoint_path):
             # Try find any .pth
             files = [f for f in os.listdir(path) if f.endswith(".pth")]
             if files: checkpoint_path = os.path.join(path, files[0])
    
    config_path = os.path.join(model_dir, "config.json")
    
    if not os.path.exists(config_path) or not os.path.exists(checkpoint_path):
        print(f"❌ SF Load Error: Missing config or checkpoint in {model_dir}")
        return None

    # Load Config
    with open(config_path, 'r') as f:
        cfg_dict = json.load(f)
    cfg = AttrDict(cfg_dict)

    return SFModelWrapper(cfg, observation_space, action_space, checkpoint_path)