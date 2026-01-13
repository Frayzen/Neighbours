from config.settings import CELL_SIZE, GRID_HEIGHT_PIX, GRID_WIDTH_PIX, DEBUG_MODE
import pygame
from core.camera import Camera
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
    UI_WEAPON_Y,
    SCREEN_WIDTH_PIX,
    SCREEN_HEIGHT_PIX
    )


class GameRenderer:
    def __init__(self, game):
        self.game = game
        self.rendering_surface = pygame.Surface((GRID_WIDTH_PIX, GRID_HEIGHT_PIX))
        self.font = pygame.font.SysFont("Arial", 24)

        self.background_world = pygame.Surface((GRID_WIDTH_PIX, GRID_HEIGHT_PIX))
        self.background_world.fill(COLOR_BACKGROUND)
        self._draw_world()

    def reload_world(self):
        self.background_world.fill(COLOR_BACKGROUND)
        self._draw_world()

    def draw(self, camera : Camera):
        self.game.screen.fill(COLOR_BACKGROUND)
        self.rendering_surface.blit(self.background_world, (0,0))

        self.cam_rect = camera.get_subregion()
        self._draw_entities()

        self.game.screen.blit(self.rendering_surface, (0,0), area=self.cam_rect)

        self.game.damage_texts.draw(self.game.screen, self.game.camera)
        vfx_manager.draw(self.game.screen, self.game.camera)
        self._draw_ui()
        
        if self.game.paused:
            self.draw_pause_menu()
            
        debug.draw(self.game.screen)
        
        if DEBUG_MODE:
            fps = self.game.clock.get_fps()
            fps_text = self.font.render(f"FPS: {int(fps)}", True, (0, 255, 0))
            # Top right corner
            rect = fps_text.get_rect(topright=(SCREEN_WIDTH_PIX - 10, 10))
            self.game.screen.blit(fps_text, rect)
            
        pygame.display.flip()

    def _draw_ui(self):
        # Common data 
        bar_width = UI_HEALTH_BAR_WIDTH
        bar_height = UI_HEALTH_BAR_HEIGHT

        # Positions
        health_x = UI_HEALTH_BAR_X
        health_y = UI_HEALTH_BAR_Y

        weapon_x = UI_WEAPON_X
        weapon_y = UI_WEAPON_Y

        # PLAYER HEALTH BAR
        pygame.draw.rect(
            self.game.screen,
            COLOR_HEALTH_BAR_BG,
            (health_x, health_y, bar_width, bar_height)
        )

        health_pct = max(
            0,
            self.game.player.health / self.game.player.max_health
        )

        pygame.draw.rect(
            self.game.screen,
            COLOR_HEALTH_BAR_FG,
            (health_x, health_y, int(bar_width * health_pct), bar_height)
        )

        pygame.draw.rect(
            self.game.screen,
            COLOR_HEALTH_BAR_BORDER,
            (health_x, health_y, bar_width, bar_height),2
        )

        # WEAPON COOLDOWN BAR
        weapon_bar_height = bar_height // 2  # smaller height for weapon bar

        pygame.draw.rect(
            self.game.screen,
            COLOR_WEAPON_BAR_BG,
            (weapon_x, weapon_y, bar_width, weapon_bar_height)
        )

        current_weapon = self.game.player.combat.current_weapon

        if current_weapon:
            elapsed = max(
                0,
                self.game.current_time - current_weapon.last_attack_time
            )

            if current_weapon.cooldown > 0:
                weapon_pct = min(
                    elapsed / current_weapon.cooldown,
                    1
                )
            else:
                weapon_pct = 1

            pygame.draw.rect(
                self.game.screen,
                COLOR_WEAPON_BAR_FG,
                (
                    weapon_x,
                    weapon_y,
                    int(bar_width * weapon_pct),
                    weapon_bar_height
                )
            )

        pygame.draw.rect(
            self.game.screen,
            COLOR_HEALTH_BAR_BORDER,
            (weapon_x, weapon_y, bar_width, weapon_bar_height),
            2
        )


        # Draw Level
        level_text = self.font.render(f"Level: {self.game.player.level}", True, (255, 255, 255))
        self.game.screen.blit(level_text, (health_x, health_y + bar_height + 5))
        
        # Draw XP Bar (Optional but nice)
        xp_pct = self.game.player.xp / self.game.player.xp_to_next_level
        pygame.draw.rect(self.game.screen, (50, 50, 50), (health_x, health_y + bar_height + 30, bar_width, 10))
        pygame.draw.rect(self.game.screen, (0, 200, 255), (health_x, health_y + bar_height + 30, int(bar_width * xp_pct), 10))
        pygame.draw.rect(self.game.screen, (255, 255, 255), (health_x, health_y + bar_height + 30, bar_width, 10), 1)

    def _draw_world(self):
        skip = 0
        for y in range(self.game.world.height):
            for x in range(self.game.world.width):
                cell = self.game.world.get_cell(x, y)
                if cell:
                    rect = pygame.Rect(
                        x * CELL_SIZE,
                        y * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE,
                    )
                    if cell.texture:
                        if (
                            cell.texture.get_width() != CELL_SIZE
                            or cell.texture.get_height() != CELL_SIZE
                        ):
                            cell.texture = pygame.transform.scale(
                                cell.texture, (CELL_SIZE, CELL_SIZE)
                            )
                        self.background_world.blit(cell.texture, rect)
                    else:
                        pygame.draw.rect(self.background_world, cell.color, rect)
        print("SKIP", skip)

    def _draw_entities(self):
        self.game.player.draw(self.rendering_surface)
        for obj in self.game.gridObjects:
            obj.draw(self.rendering_surface)
        for proj in self.game.projectiles:
            proj.draw(self.rendering_surface)

    def draw_pause_menu(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH_PIX, SCREEN_HEIGHT_PIX))
        overlay.set_alpha(180) # 0-255
        overlay.fill((0, 0, 0))
        self.game.screen.blit(overlay, (0, 0))
        
        # Menu Title
        title_font = pygame.font.SysFont("Arial", 48, bold=True)
        title_text = title_font.render("PAUSED", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH_PIX // 2, 80))
        self.game.screen.blit(title_text, title_rect)
        
        # Stats
        player = self.game.player
        stats = [
            f"Health: {int(player.health)} / {player.max_health}",
            f"Level: {player.level}",
            f"XP: {player.xp} / {player.xp_to_next_level}",
            f"Speed: {player.speed * player.speed_mult:.1f}",
            f"Damage: x{player.damage_mult:.2f}",
            f"Defense: x{player.defense_mult:.2f}",
            f"Cooldown: x{player.cooldown_mult:.2f}",
            f"Luck: x{player.luck_mult:.2f}"
        ]
        
        # Stats Position - Shifted UP
        start_y = 150 
        line_height = 35
        
        for i, stat in enumerate(stats):
            text = self.font.render(stat, True, (200, 200, 200))
            rect = text.get_rect(center=(SCREEN_WIDTH_PIX // 2, start_y + i * line_height))
            self.game.screen.blit(text, rect)
            
        # Border around stats
        stats_height = len(stats) * line_height
        border_rect = pygame.Rect(SCREEN_WIDTH_PIX//2 - 150, start_y - 10, 300, stats_height + 20)
        pygame.draw.rect(self.game.screen, (255, 255, 255), border_rect, 2)
        
        # Buttons Position - Shifted DOWN
        # Button data (must match logic.py)
        btn_w = 200
        btn_h = 50
        btn_y = SCREEN_HEIGHT_PIX - 250
        
        # Save Button
        save_x = SCREEN_WIDTH_PIX//2 - btn_w//2 - 110
        save_rect = pygame.Rect(save_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(self.game.screen, (50, 200, 50), save_rect)
        pygame.draw.rect(self.game.screen, (255, 255, 255), save_rect, 2)
        save_text = self.font.render("Save Game", True, (255, 255, 255))
        save_text_rect = save_text.get_rect(center=save_rect.center)
        self.game.screen.blit(save_text, save_text_rect)

        # Close Button
        close_x = SCREEN_WIDTH_PIX//2 + 10
        close_rect = pygame.Rect(close_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(self.game.screen, (200, 50, 50), close_rect)
        pygame.draw.rect(self.game.screen, (255, 255, 255), close_rect, 2)
        close_text = self.font.render("Close Game", True, (255, 255, 255))
        close_text_rect = close_text.get_rect(center=close_rect.center)
        self.game.screen.blit(close_text, close_text_rect)

        # New Game Button (Restart)
        new_y = btn_y + 70
        new_rect = pygame.Rect(SCREEN_WIDTH_PIX//2 - btn_w//2, new_y, btn_w, btn_h)
        pygame.draw.rect(self.game.screen, (100, 100, 200), new_rect)
        pygame.draw.rect(self.game.screen, (255, 255, 255), new_rect, 2)
        new_text = self.font.render("New Game", True, (255, 255, 255))
        new_rect_center = new_text.get_rect(center=new_rect.center)
        self.game.screen.blit(new_text, new_rect_center)
        
        # Draw Start Menu overlay if active (renderer needs to know)
        # ^ This line might be redundant if we call this FROM draw_start_menu which is called by Game

