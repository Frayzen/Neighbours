from typing import List, Optional, Tuple
from config.settings import GRID_HEIGHT, GRID_WIDTH


class Cell:
    def __init__(
        self,
        name,
        walkable=True,
        texture_path="",
        color=(255, 255, 255),
        width=1,
        height=1,
        trigger=None,
    ):
        self.name = name
        self.walkable = walkable
        self.texture_path = texture_path
        self.color = color
        self.width = width
        self.height = height
        self.trigger = trigger
        self.texture = None  # Will hold the pygame Surface

    def __str__(self):
        return self.name


class World:
    def __init__(self, width=GRID_WIDTH, height=GRID_HEIGHT):
        self.width = width
        self.height = height
        # Grid stores tuples: (Cell, (offset_x, offset_y))
        # Default empty cell
        empty_cell = Cell("Empty", color=(0, 0, 0))
        self.grid: List[List[Tuple[Cell, Tuple[int, int]]]] = [
            [(empty_cell, (0, 0)) for _ in range(width)] for _ in range(height)
        ]
        self.spawn_points = []

    def set_cell(self, x, y, cell):
        if 0 <= x < self.width and 0 <= y < self.height:
            # Check bounds for multi-tile objects
            if x + cell.width > self.width or y + cell.height > self.height:
                print(f"Cannot place {cell.name} at ({x}, {y}): Out of bounds.")
                return

            # Place the object
            for h in range(cell.height):
                for w in range(cell.width):
                    self.grid[y + h][x + w] = (cell, (w, h))
        else:
            print(f"Coordinates ({x}, {y}) are out of bounds.")

    def get_cell(self, x, y) -> Optional[Cell]:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x][0]  # Return just the cell
        return None

    def get_cell_full(self, x, y):
        """Returns (Cell, (offset_x, offset_y))"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def display(self):
        for row in self.grid:
            print(" ".join(str(cell[0]) for cell in row))
