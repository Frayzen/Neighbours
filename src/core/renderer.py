from config.settings import CELL_SIZE
import pygame
from core.debug import debug


class GameRenderer:
    def __init__(self, game):
        self.game = game

    def draw(self):
        self.game.screen.fill("black")
        self._draw_world()
        self._draw_entities()
        debug.draw(self.game.screen)
        pygame.display.flip()

    def _draw_world(self):
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
                        self.game.screen.blit(cell.texture, rect)
                    else:
                        pygame.draw.rect(self.game.screen, cell.color, rect)

    def _draw_entities(self):
        self.game.player.draw(self.game.screen)
        for obj in self.game.gridObjects:
            obj.draw(self.game.screen)
