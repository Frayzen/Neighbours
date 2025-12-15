import pygame
from core.debug import debug
from core.vfx import vfx_manager
from combat.weapon import Weapon
from combat.combat_manager import CombatManager
from config.settings import (
    COLOR_BACKGROUND, 
    COLOR_HEALTH_BAR_BG, 
    COLOR_HEALTH_BAR_FG, 
    COLOR_HEALTH_BAR_BORDER,
    COLOR_WEAPON_BAR_BG,
    COLOR_WEAPON_BAR_FG,
    UI_HEALTH_BAR_WIDTH,
    UI_HEALTH_BAR_HEIGHT,
    UI_HEALTH_BAR_X,
    UI_HEALTH_BAR_Y,
    UI_WEAPON_BAR_X,
    UI_WEAPON_BAR_Y,
    UI_WEAPON_X,
    UI_WEAPON_Y
    )

class GameRenderer:
    def __init__(self, game):
        self.game = game

    def draw(self):
        self.game.screen.fill(COLOR_BACKGROUND)
        self._draw_world()
        self._draw_entities()
        vfx_manager.draw(self.game.screen)
        self._draw_ui()
        debug.draw(self.game.screen)
        pygame.display.flip()

    def _draw_ui(self):
        #commun data for health bar and weapon display
        bar_width = UI_HEALTH_BAR_WIDTH
        bar_height = UI_HEALTH_BAR_HEIGHT
        # Draw Health Bar
        x = UI_HEALTH_BAR_X
        y = UI_HEALTH_BAR_Y
        #for the weapon display
        x2= UI_WEAPON_X
        y2= UI_WEAPON_Y
        
        # Background (Red)
        pygame.draw.rect(self.game.screen, COLOR_HEALTH_BAR_BG, (x, y, bar_width, bar_height))
        pygame.draw.rect(self.game.screen, COLOR_WEAPON_BAR_BG, (x2, y2, bar_width, bar_height))
        
        # Foreground (Green)
        health_pct = max(0, self.game.player.health / self.game.player.max_health)
        pygame.draw.rect(self.game.screen, COLOR_HEALTH_BAR_FG, (x, y, int(bar_width * health_pct), bar_height))

        # Weapons if the player hold one
        current_weapon = self.game.player.combat.current_weapon
        if current_weapon:
            elapsed = self.game.current_time - current_weapon.last_attack_time
            weapon_pct = min(1, elapsed / current_weapon.cooldown) if current_weapon.cooldown > 0 else 1
            pygame.draw.rect(self.game.screen, COLOR_WEAPON_BAR_FG, (x2, y2, int(bar_width * weapon_pct), bar_height))

        
        # Border (White)
        pygame.draw.rect(self.game.screen, COLOR_HEALTH_BAR_BORDER, (x, y, bar_width, bar_height), 2)

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
