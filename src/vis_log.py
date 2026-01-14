import pygame
import csv
import os
import sys
import numpy as np

import glob

# Adjust path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ai.brain_vis import BrainVisualizer

def run():
    pygame.init()
    
    # Setup Window
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI Brain Replay")
    
    pygame.display.set_caption("AI Brain Replay")
    
    # Load Latest Log
    log_dir = "logs"
    csv_files = glob.glob(os.path.join(log_dir, "*.csv"))
    
    if not csv_files:
        print(f"No log files found in {log_dir}")
        return
        
    # Sort by modification time
    latest_log = max(csv_files, key=os.path.getmtime)
    print(f"Opening latest log: {latest_log}")
    
    log_path = latest_log

    rows = []
    try:
        with open(log_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except Exception as e:
        print(f"Error reading log: {e}")
        return
        
    if not rows:
        print("Log is empty.")
        return
        
    print(f"Loaded {len(rows)} frames from {log_path}")
    
    # Setup Visualizers
    # We want Split Screen: [ BOSS BRAIN ] | [ PLAYER BRAIN ]
    # Each is 600 wide. So window need 1250 wide or so.
    
    VIS_W = 600
    VIS_H = 500
    MARGIN = 20
    
    WIDTH = VIS_W * 2 + MARGIN * 3
    HEIGHT = VIS_H + 80
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI Brain Replay - Duel View")
    
    brain_boss = BrainVisualizer(x=MARGIN, y=MARGIN, width=VIS_W, height=VIS_H)
    brain_player = BrainVisualizer(x=MARGIN*2 + VIS_W, y=MARGIN, width=VIS_W, height=VIS_H)
    
    clock = pygame.time.Clock()
    running = True
    idx = 0
    paused = False
    speed = 1.0 # Frames per tick (accumulator)
    idx_float = 0.0 # For smooth speed control
    
    font_ui = pygame.font.SysFont("Consolas", 14)
    font_large = pygame.font.SysFont("Consolas", 20, bold=True)
    
    while running:
        screen.fill((30, 30, 30))
        
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_RIGHT:
                    if paused: idx = min(idx + 1, len(rows) - 1)
                    else: idx = min(idx + 60, len(rows) - 1)
                    idx_float = float(idx)
                elif event.key == pygame.K_LEFT:
                    if paused: idx = max(idx - 1, 0)
                    else: idx = max(idx - 60, 0)
                    idx_float = float(idx)
                elif event.key == pygame.K_UP:
                    speed = min(speed * 1.5, 10.0)
                elif event.key == pygame.K_DOWN:
                    speed = max(speed / 1.5, 0.1)
                elif event.key == pygame.K_r: # Reset
                    idx = 0
                    idx_float = 0.0
                    
        # Update Replay
        if not paused and idx < len(rows):
            idx_float += speed
            idx = int(idx_float)
            
        # Clamp
        if idx >= len(rows): 
            idx = len(rows) - 1
            if not paused: paused = True # Auto-pause at end
            
        # Parse Row
        row = rows[idx]
        
        # WE NEED TO DETECT IF IT IS NEW FORMAT (DUAL) OR OLD FORMAT (SINGLE)
        is_dual = "b_obs_0" in row
        
        if is_dual:
            # BOSS DATA
            b_obs = []
            for i in range(33):
                col = f"b_obs_{i}"
                if col in row: b_obs.append(float(row[col]))
            b_obs_arr = np.array(b_obs, dtype=np.float32)
            b_act = int(row.get("act_boss", 0))
            
            # PLAYER DATA
            p_obs = []
            for i in range(33):
                col = f"p_obs_{i}"
                if col in row: p_obs.append(float(row[col]))
            p_obs_arr = np.array(p_obs, dtype=np.float32)
            p_act = int(row.get("act_player", 0))
            
            # Draw Both
            brain_boss.draw(screen, None, b_obs_arr, last_action=b_act)
            brain_player.draw(screen, None, p_obs_arr, last_action=p_act)
            
            # Labels
            t_boss = font_large.render("BOSS AGENT", True, (255, 100, 100))
            t_player = font_large.render("PLAYER AGENT", True, (100, 255, 100))
            screen.blit(t_boss, (MARGIN, MARGIN - 20)) # A bit high, might be clipped, let's just overlay or depend on brain title
            
        else:
            # FALLBACK TO OLD FORMAT
            obs = []
            for i in range(33):
                col = f"obs_{i}"
                if col in row: obs.append(float(row[col]))
            obs_arr = np.array(obs, dtype=np.float32)
            action = int(row.get("action", 0))
            
            brain_boss.draw(screen, None, obs_arr, last_action=action)
            t_legacy = font_large.render("LEGACY LOG (SINGLE AGENT)", True, (200, 200, 200))
            screen.blit(t_legacy, (MARGIN, HEIGHT - 100))

        # --- DRAW UI OVERLAY ---
        ui_y = HEIGHT - 60
        pygame.draw.rect(screen, (50, 50, 50), (0, ui_y, WIDTH, 60))
        pygame.draw.line(screen, (100, 100, 100), (0, ui_y), (WIDTH, ui_y), 1)
        
        # Progress Bar
        bar_x = 10
        bar_y = ui_y + 10
        bar_w = WIDTH - 20
        bar_h = 10
        
        pygame.draw.rect(screen, (20, 20, 20), (bar_x, bar_y, bar_w, bar_h))
        if len(rows) > 0:
            progress = idx / len(rows)
            pygame.draw.rect(screen, (0, 200, 255), (bar_x, bar_y, int(bar_w * progress), bar_h))
        
        # Info Text
        status = "PAUSED" if paused else f"PLAYING ({speed:.1f}x)"
        ts = row.get("timestamp", idx)
        
        info_str = f"Frame: {idx}/{len(rows)} | Tick: {ts} | Status: {status}"
        controls_str = "Controls: SPACE=Pause | LEFT/RIGHT=Seek/Step | UP/DOWN=Speed | R=Reset"
        
        t1 = font_ui.render(info_str, True, (255, 255, 255))
        t2 = font_ui.render(controls_str, True, (180, 180, 180))
        
        screen.blit(t1, (10, ui_y + 25))
        screen.blit(t2, (10, ui_y + 42))

        pygame.display.flip()
        clock.tick(60) # Main loop always 60 FPS, replay speed handled by idx logic
        
    pygame.quit()

if __name__ == "__main__":
    run()
