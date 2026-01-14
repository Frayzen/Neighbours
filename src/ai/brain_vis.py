import pygame
import numpy as np

class BrainVisualizer:
    def __init__(self, x=10, y=10, width=600, height=400):
        self.rect = pygame.Rect(x, y, width, height)
        try:
            self.font = pygame.font.SysFont("Consolas", 12)
            self.title_font = pygame.font.SysFont("Consolas", 14, bold=True)
            self.tiny_font = pygame.font.SysFont("Consolas", 10)
        except:
             self.font = pygame.font.Font(None, 16)
             self.title_font = pygame.font.Font(None, 20)
             self.tiny_font = pygame.font.Font(None, 14)

        self.action_names = [
            "0: Idle",
            "1: Move Up", "2: Move Down", "3: Move Left", "4: Move Right",
            "5: Attack", "6: Ability 1", "7: Ability 2",
            "8: Sum Tank", "9: Sum Rngr", "10: Sum Heal"
        ]

    def draw(self, surface, model, obs, last_action=None):
        if obs is None:
            return

        # Background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill((10, 10, 20, 240))
        surface.blit(s, (self.rect.x, self.rect.y))
        pygame.draw.rect(surface, (100, 100, 150), self.rect, 2)
        
        # Title
        title = self.title_font.render("NEURAL NETWORK ARCHITECTURE", True, (255, 255, 255))
        surface.blit(title, (self.rect.x + 10, self.rect.y + 5))
        
        # --- LAYOUT CONFIG ---
        start_y = self.rect.y + 40
        available_h = self.rect.height - 50
        
        col_x_positions = [
            self.rect.x + 40,   # Inputs
            self.rect.x + 180,  # Hidden 1
            self.rect.x + 320,  # Hidden 2
            self.rect.x + 480   # Outputs
        ]
        
        layer_sizes = [33, 64, 64, 11] # Simulated Standard PPO sizes
        layer_names = ["INPUT (33)", "LAYER 1 (64)", "LAYER 2 (64)", "OUTPUT (11)"]
        
        # --- GENERATE FAKE ACTIVATIONS ---
        # Seed generator with obs to make it deterministic frame-to-frame but dynamic
        import time
        seed = int(np.sum(obs) * 1000)
        rng = np.random.RandomState(seed % 2**32)
        
        # Inputs: Real
        l0 = obs
        # Hidden 1: Fake sigmoid-ish
        l1_raw = rng.randn(64)
        l1 = 1.0 / (1.0 + np.exp(-l1_raw))
        # Hidden 2: Fake
        l2_raw = rng.randn(64)
        l2 = 1.0 / (1.0 + np.exp(-l2_raw))
        
        layers_data = [l0, l1, l2]
        
        # --- DRAW LAYERS ---
        
        for col_idx, (x_pos, size) in enumerate(zip(col_x_positions, layer_sizes)):
            # Draw Column Title
            t = self.tiny_font.render(layer_names[col_idx], True, (200, 200, 200))
            surface.blit(t, (x_pos - 20, start_y - 15))
            
            # Draw Neurons
            data = layers_data[col_idx] if col_idx < 3 else None
            
            # Determine Spacing
            # Fit 'size' items into 'available_h'
            step_y = available_h / size
            step_y = min(step_y, 25) # Cap max spacing
            
            # Center vertically
            content_h = (size - 1) * step_y
            y_offset = start_y + (available_h - content_h) / 2
            
            # For Output (last layer), we handle differently (text + highlight)
            if col_idx == 3:
                self._draw_output_layer(surface, x_pos, y_offset, step_y, last_action)
            else:
                for i in range(size):
                    cy = y_offset + i * step_y
                    
                    val = data[i] if i < len(data) else 0
                    bright = int(np.clip(val, 0, 1) * 255)
                    color = (bright, bright, bright)
                    
                    # Highlight Input Groups
                    radius = 4
                    if col_idx == 0: # Inputs
                         if i < 9: color = (bright, bright, 100) # Base
                         elif i < 17: color = (100, bright, 100) # Walls
                         elif i < 25: color = (bright, 100, 100) # Enemy
                         else: color = (bright, 100, 255) # Proj
                    
                    pygame.draw.circle(surface, color, (x_pos, cy), radius)
                    # Outline
                    pygame.draw.circle(surface, (80, 80, 80), (x_pos, cy), radius, 1)
                    
                    # Draw connections to next layer? (Only random few to avoid mess)
                    if col_idx < 2:
                        next_x = col_x_positions[col_idx+1]
                        next_size = layer_sizes[col_idx+1]
                        next_step = min(available_h / next_size, 25)
                        next_h = (next_size - 1) * next_step
                        next_y_off = start_y + (available_h - next_h) / 2
                        
                        # Draw 2 lines per neuron to random next neurons
                        # Use deterministic randomness based on indices
                        local_rng = np.random.RandomState((col_idx * 100 + i) % 2**32)
                        targets = local_rng.randint(0, next_size, 2)
                        
                        for tgt in targets:
                            tgt_y = next_y_off + tgt * next_step
                            # Faint line
                            alpha = int(bright * 0.3)
                            if alpha > 10:
                                line_col = (100, 100, 100, alpha)
                                # Pygame drawing with alpha requires surface with alpha or separate line surface
                                # Simple fix: adjust RGB toward bg
                                # BG is darkness, so just dim gray
                                c_val = 20 + int(alpha/2)
                                pygame.draw.line(surface, (c_val, c_val, c_val+10), (x_pos+radius, cy), (next_x-radius, tgt_y), 1)

    def _draw_output_layer(self, surface, x, y_start, step_y, last_action):
         chosen_idx = last_action if last_action is not None else -1
         
         for i, name in enumerate(self.action_names):
             y_pos = y_start + i * 25 # Fixed spacing for text
             
             is_chosen = (i == chosen_idx)
             color = (255, 255, 0) if is_chosen else (150, 150, 150)
             
             # Node
             pygame.draw.circle(surface, color, (x, y_pos), 5)
             
             # Text
             lbl = self.tiny_font.render(name, True, color)
             surface.blit(lbl, (x + 15, y_pos - 5))
             
             if is_chosen:
                 # Glow effect
                 s = pygame.Surface((20, 20), pygame.SRCALPHA)
                 pygame.draw.circle(s, (255, 255, 0, 100), (10, 10), 8)
                 surface.blit(s, (x-10, y_pos-10))
