import pygame

from core.camera import Camera
from core.setup import GameSetup
from core.renderer import GameRenderer
from core.logic import GameLogic
from config.settings import FPS
from core.damages_text import DamageTexts


class Game:

    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.player = None

        # Level Management
        from core.level_manager import LevelManager
        self.level_manager = LevelManager()

        # Perform initial setup
        self.current_layer_index = 0 # DEPRECATED: Use level_manager.get_level_index() logic
        self.setup = GameSetup(self)
        self.setup.perform_setup()

        # Initialize subsystems
        self.renderer = GameRenderer(self)
        self.logic = GameLogic(self)
        self.current_time = 0
        self.start_time = pygame.time.get_ticks() # Track run duration
        self.end_time = 0
        self.camera = Camera()
        self.damage_texts = DamageTexts()
        self.enemies = []
        self.projectiles = []

        self.paused = False
        self.game_over = False
        self.victory = False

        # Debug
        self.show_debug_path = False
        self.debug_path_points = []

        # Auto-load logic
        from core.save_manager import SaveManager

        if SaveManager.has_save_file():
            print("DEBUG: Save file found. Auto-loading...")
            if SaveManager.load_game(self):
                self.paused = True  # Start in pause menu as requested
            else:
                print("DEBUG: Load failed. Starting fresh.")
                self.paused = False
                self.restart_game()
        else:
            print("DEBUG: No save file. Starting fresh.")
            # Initial setup was already done at line 24-25, so we just proceed
            self.paused = False

    def restart_game(self):
        print("DEBUG: Restarting Game...")
        self.game_over = False
        self.victory = False
        self.paused = False
        
        # Reset basic stats
        self.current_layer_index = 0
        self.level_manager.current_level_index = 0
        
        # Re-run setup
        self.setup.perform_setup()
        
        # Re-init logic to bind new player/entities
        self.logic = GameLogic(self)
        
        self.start_time = pygame.time.get_ticks()
        self.end_time = 0

    def trigger_game_over(self):
        if not self.victory:
            self.game_over = True
            self.end_time = pygame.time.get_ticks()
            
    def trigger_victory(self):
        if not self.game_over:
            self.victory = True
            self.end_time = pygame.time.get_ticks()

    def get_run_time_string(self):
        if self.end_time > 0:
            millis = self.end_time - self.start_time
        else:
            # Fallback if called during gameplay or logic update
            # Use current_time which matches the frame time
            millis = self.current_time - self.start_time
            
        seconds = int(millis / 1000)
        minutes = int(seconds / 60)
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def next_layer(self):
        if not self.level_manager.advance_level():
            print("DEBUG: No more levels! Game Over or Loop?")
            return

        self.current_layer_index = self.level_manager.get_level_index()
        print(f"DEBUG: Generating level {self.current_layer_index}...")
        
        level_config = self.level_manager.get_current_level()
        
        # Determine player health and other persistent state if needed
        # For now, we just regenerate the world
        self.world = self.setup.world_loader.generate(level_config)
        
        # Re-initialize entities for the new layer (Preserve Player)
        self.setup.respawn_player() 
        
        # Important: Update logic with new references if needed
        self.logic = GameLogic(self)
        
        # Reload renderer cache
        self.renderer.reload_world()
        
        print(f"DEBUG: Layer {self.current_layer_index} generated.")

    def run(self):
        running = True
        # Main game loop
        while running:
            self.current_time = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                         if not self.game_over and not self.victory:
                             self.paused = not self.paused
                    
                    if (self.game_over or self.victory) and event.key == pygame.K_r:
                        self.restart_game()

                    # Debug
                    if event.key == pygame.K_F1:
                         self.show_debug_path = not self.show_debug_path
                    
                    if event.key == pygame.K_h:
                         # Toggle all debug
                         pass
                    
                # Pass events to subsystems if not paused/gameover (or specific events)
                if self.paused:
                     self.logic.handle_pause_input(event)

                if not self.paused and not self.game_over and not self.victory:
                    self.logic.handle_event(event)

            # Update Logic (only if playing)
            if not self.paused and not self.game_over and not self.victory:
                self.logic.update(self.current_time)
                self.damage_texts.update()
            
            # Helper for camera debug
            if self.show_debug_path:
                 pass

            # Update Camera
            self.camera.update(self.player)
            
            # Draw
            self.renderer.draw(self.camera)

            self.clock.tick(FPS)
            # print(self.clock.get_fps())
        pygame.quit()


gameInstance = Game()
