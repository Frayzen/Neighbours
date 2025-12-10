class Environment:
    def __init__(self, name, walkable=True, texture_path="", color=(255, 255, 255), width=1, height=1, trigger=None):
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
    def __init__(self, width=32, height=32):
        self.width = width
        self.height = height
        # Grid stores tuples: (Environment, (offset_x, offset_y))
        # Default empty environment
        empty_env = Environment("Empty", color=(0, 0, 0))
        self.grid = [[(empty_env, (0, 0)) for _ in range(width)] for _ in range(height)]

    def set_environment(self, x, y, environment):
        if 0 <= x < self.width and 0 <= y < self.height:
            # Check bounds for multi-tile objects
            if x + environment.width > self.width or y + environment.height > self.height:
                print(f"Cannot place {environment.name} at ({x}, {y}): Out of bounds.")
                return

            # Place the object
            for h in range(environment.height):
                for w in range(environment.width):
                    self.grid[y + h][x + w] = (environment, (w, h))
        else:
            print(f"Coordinates ({x}, {y}) are out of bounds.")

    def get_environment(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x][0] # Return just the environment
        return None

    def get_environment_full(self, x, y):
        """Returns (Environment, (offset_x, offset_y))"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return None

    def display(self):
        for row in self.grid:
            print(" ".join(str(cell) for cell in row))

