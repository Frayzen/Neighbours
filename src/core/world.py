class Environment:
    def __init__(self, name, walkable=True, texture_path="", color=(255, 255, 255)):
        self.name = name
        self.walkable = walkable
        self.texture_path = texture_path
        self.color = color
        self.texture = None  # Will hold the pygame Surface

    def __str__(self):
        return self.name

class World:
    def __init__(self, width=32, height=32):
        self.width = width
        self.height = height
        self.grid = [[Environment("Empty", color=(0, 0, 0)) for _ in range(width)] for _ in range(height)]

    def set_environment(self, x, y, environment):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = environment
        else:
            print(f"Coordinates ({x}, {y}) are out of bounds.")

    def get_environment(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def display(self):
        for row in self.grid:
            print(" ".join(str(cell) for cell in row))

