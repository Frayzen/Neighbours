from config.settings import GRID_HEIGHT, GRID_WIDTH, ROOM_AMOUNT, ROOM_EXTRA_SIZE
from core.registry import Registry
from random import randint
from core.world import World
from typing import List, Tuple


def quadrangle_intersect(quadA, quadB):
    ax, ay, aw, ah = quadA
    bx, by, bw, bh = quadB

    if ax + aw <= bx or bx + bw <= ax:
        return False
    if ay + ah <= by or by + bh <= ay:
        return False

    return True


class WorldLoader:
    def __init__(self):
        self.world = World()

        # Get cells from Registry
        self.grass = Registry.get_cell("Grass")
        self.wall = Registry.get_cell("Wall")
        self.water = Registry.get_cell("Water")
        self.door = Registry.get_cell("Door")

        # Region tracking (Option A)
        self.regions = [[None for _ in range(self.world.width)]
                        for _ in range(self.world.height)]
        self.current_region = -1

    # -------------------------------------------------------------------------
    # REGION HELPERS
    # -------------------------------------------------------------------------
    def _start_region(self):
        self.current_region += 1

    def _carve(self, x, y, cell_type=None):
        if cell_type is None:
            cell_type = self.grass
        self.world.set_cell(x, y, cell_type)
        self.regions[y][x] = self.current_region

    # -------------------------------------------------------------------------
    # MAIN GENERATOR
    # -------------------------------------------------------------------------
    def generate(self):

        # Fill background with wall
        for y in range(self.world.height):
            for x in range(self.world.width):
                self.world.set_cell(x, y, self.wall)

        self.__generate_rooms()

        # Fill unused space with mazes
        for x in range(1, GRID_WIDTH, 2):
            for y in range(1, GRID_HEIGHT, 2):
                if self.world.get_cell(x, y) != self.wall:
                    continue
                self.__growMaze(x, y)

        # Connect regions & remove dead ends
        self.__connect_regions()
        self.__remove_dead_ends()

        return self.world

    # -------------------------------------------------------------------------
    # GROWING TREE / MAZE
    # -------------------------------------------------------------------------
    def __growMaze(self, x, y):
        """
        Implements the growing tree algorithm for maze generation.
        Starts at (x, y) and carves a maze using a depth-first approach.
        """

        self._start_region()
        self._carve(x, y)

        cells = [(x, y)]

        directions = [(0, -1), (0, 1), (1, 0), (-1, 0)]  # move 1 step; carve 2 steps

        while cells:
            cx, cy = cells[-1]

            # Shuffle directions
            shuffled = list(directions)
            for i in range(len(shuffled)):
                j = randint(0, len(shuffled) - 1)
                shuffled[i], shuffled[j] = shuffled[j], shuffled[i]

            carved = False
            for dx, dy in shuffled:
                if self._can_carve(cx, cy, dx, dy):
                    # midpoint between cx,cy and destination
                    mx = cx + dx
                    my = cy + dy
                    nx = cx + dx * 2
                    ny = cy + dy * 2

                    self._carve(mx, my)
                    self._carve(nx, ny)

                    cells.append((nx, ny))
                    carved = True
                    break

            if not carved:
                cells.pop()

    def _can_carve(self, x, y, dx, dy):
        # Destination 2 tiles away
        nx = x + dx * 2
        ny = y + dy * 2

        if not (0 <= nx < self.world.width and 0 <= ny < self.world.height):
            return False

        return self.world.get_cell(nx, ny) == self.wall

    # -------------------------------------------------------------------------
    # ROOM GENERATOR
    # -------------------------------------------------------------------------
    def __generate_rooms(self):
        self.rooms: List[Tuple[int, int, int, int]] = []

        for _ in range(ROOM_AMOUNT):

            size = randint(1, 3 + ROOM_EXTRA_SIZE) * 2 + 1
            width = size
            height = size

            rectangularity = randint(0, 1 + size // 2) * 2
            if randint(0, 1) == 0:
                width += rectangularity
            else:
                height += rectangularity

            x = randint(0, (GRID_WIDTH - width) // 2) * 2 + 1
            y = randint(0, (GRID_HEIGHT - height) // 2) * 2 + 1
            current = (x, y, width, height)

            intersects = False
            for other in self.rooms:
                if quadrangle_intersect(current, other):
                    intersects = True
                    break
            if intersects:
                continue

            self.rooms.append(current)

            self._start_region()
            for dx in range(width):
                for dy in range(height):
                    self._carve(x + dx, y + dy)

    # -------------------------------------------------------------------------
    # CONNECT REGIONS
    # -------------------------------------------------------------------------
    def __connect_regions(self):
        connector_regions = {}

        # Evaluate all possible connectors
        for y in range(1, self.world.height - 1):
            for x in range(1, self.world.width - 1):

                if self.world.get_cell(x, y) != self.wall:
                    continue

                touching = set()
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    rid = self.regions[y + dy][x + dx]
                    if rid is not None:
                        touching.add(rid)

                if len(touching) >= 2:
                    connector_regions[(x, y)] = touching

        connectors = list(connector_regions.keys())

        merged = {i: i for i in range(self.current_region + 1)}
        open_regions = set(merged.values())

        while len(open_regions) > 1:
            cx, cy = connectors[randint(0, len(connectors) - 1)]

            self._add_junction(cx, cy)

            regions_here = {merged[r] for r in connector_regions[(cx, cy)]}
            dest = next(iter(regions_here))
            sources = list(regions_here - {dest})

            for i in merged:
                if merged[i] in sources:
                    merged[i] = dest

            open_regions -= set(sources)

            # Filter connectors
            new_list = []
            for (x, y) in connectors:

                # Prevent connectors right next to each other
                if abs(x - cx) + abs(y - cy) < 2:
                    continue

                rset = {merged[r] for r in connector_regions[(x, y)]}

                if len(rset) == 1:
                    # Optional loop creation
                    if randint(1, 20) == 1:
                        self._add_junction(x, y)
                    continue

                new_list.append((x, y))

            connectors = new_list

    # -------------------------------------------------------------------------
    # JUNCTION (DOOR OR OPENING)
    # -------------------------------------------------------------------------
    def _add_junction(self, x, y):
        # 1/4 chance of being open path or open door
        if randint(1, 4) == 1:
            if randint(1, 3) == 1:
                self.world.set_cell(x, y, self.door)
            else:
                self.world.set_cell(x, y, self.grass)
        else:
            # Mostly closed doors
            self.world.set_cell(x, y, self.door)

    # -------------------------------------------------------------------------
    # DEAD-END REMOVAL
    # -------------------------------------------------------------------------
    def __remove_dead_ends(self):
        done = False

        while not done:
            done = True
            for y in range(1, self.world.height - 1):
                for x in range(1, self.world.width - 1):

                    if self.world.get_cell(x, y) == self.wall:
                        continue

                    exits = 0
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        if self.world.get_cell(x + dx, y + dy) != self.wall:
                            exits += 1

                    if exits == 1:  # dead end
                        done = False
                        self.world.set_cell(x, y, self.wall)

