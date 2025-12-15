import pygame
from core.debug import debug
from core.vfx import vfx_manager
from config.settings import (
    COLOR_BACKGROUND, 
    COLOR_HEALTH_BAR_BG, 
    COLOR_HEALTH_BAR_FG, 
    COLOR_HEALTH_BAR_BORDER,
    UI_HEALTH_BAR_WIDTH,
    UI_HEALTH_BAR_HEIGHT,
    UI_HEALTH_BAR_X,
    UI_HEALTH_BAR_Y
)

class GameRenderer:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.SysFont("Arial", 24)

    def draw(self):
        self.game.screen.fill(COLOR_BACKGROUND)
        self._draw_world()
        self._draw_entities()
        vfx_manager.draw(self.game.screen)
        self._draw_ui()
        debug.draw(self.game.screen)
        pygame.display.flip()

    def _draw_ui(self):
        # Draw Health Bar
        bar_width = UI_HEALTH_BAR_WIDTH
        bar_height = UI_HEALTH_BAR_HEIGHT
        x = UI_HEALTH_BAR_X
        y = UI_HEALTH_BAR_Y
        
        # Background (Red)
        pygame.draw.rect(self.game.screen, COLOR_HEALTH_BAR_BG, (x, y, bar_width, bar_height))
        
        # Foreground (Green)
        health_pct = max(0, self.game.player.health / self.game.player.max_health)
        pygame.draw.rect(self.game.screen, COLOR_HEALTH_BAR_FG, (x, y, int(bar_width * health_pct), bar_height))
        
        # Border (White)
        pygame.draw.rect(self.game.screen, COLOR_HEALTH_BAR_BORDER, (x, y, bar_width, bar_height), 2)

        # Draw Level
        level_text = self.font.render(f"Level: {self.game.player.level}", True, (255, 255, 255))
        self.game.screen.blit(level_text, (x, y + bar_height + 5))
        
        # Draw XP Bar (Optional but nice)
        xp_pct = self.game.player.xp / self.game.player.xp_to_next_level
        pygame.draw.rect(self.game.screen, (50, 50, 50), (x, y + bar_height + 30, bar_width, 10))
        pygame.draw.rect(self.game.screen, (0, 200, 255), (x, y + bar_height + 30, int(bar_width * xp_pct), 10))
        pygame.draw.rect(self.game.screen, (255, 255, 255), (x, y + bar_height + 30, bar_width, 10), 1)

    def _draw_world(self):
        for y in range(self.game.world.height):
            for x in range(self.game.world.width):
                cell = self.game.world.get_cell(x, y)
                if cell:
                    rect = pygame.Rect(
                        self.game.start_x + x * self.game.tile_size, 
                        self.game.start_y + y * self.game.tile_size, 
                        self.game.tile_size, 
                        self.game.tile_size
                    )
                    
                    if cell.texture:
                        if cell.texture.get_width() != self.game.tile_size or cell.texture.get_height() != self.game.tile_size:
                            cell.texture = pygame.transform.scale(cell.texture, (self.game.tile_size, self.game.tile_size))
                        self.game.screen.blit(cell.texture, rect)
                    else:
                        pygame.draw.rect(self.game.screen, cell.color, rect)

    def _draw_entities(self):
        self.game.player.draw(self.game.screen, self.game.tile_size)
        for obj in self.game.gridObjects:
            obj.draw(self.game.screen, self.game.tile_size)
