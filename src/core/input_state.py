class InputState:
    def __init__(self):
        self.move_x = 0  # -1, 0, or 1
        self.move_y = 0  # -1, 0, or 1
        self.attack = False
        self.dash = False
        self.summon = False # For boss/minion logic if needed, but starting simple
