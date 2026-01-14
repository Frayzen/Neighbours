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
        self.spawner = Registry.get_cell("Spawner")

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
    def generate(self, layer_index=0):
        self.world = World() # Reset world for new layer
        # Reset regions
        self.regions = [[None for _ in range(self.world.width)]
                        for _ in range(self.world.height)]
        self.current_region = -1
        self.rooms = [] # Reset rooms

        if layer_index == 0:
            self._generate_overworld()
        else:
            self._generate_dungeon()
            
        return self.world

    def _generate_overworld(self):
        # 1. Fill background with wall (or empty, but wall is safer for boundary)
        for y in range(self.world.height):
            for x in range(self.world.width):
                self.world.set_cell(x, y, self.wall)
                
        # 2. Create 25x25 Grass Box
        # Center it
        start_x = (GRID_WIDTH - 25) // 2
        start_y = (GRID_HEIGHT - 25) // 2
        
        self._start_region()
        for y in range(start_y, start_y + 25):
            for x in range(start_x, start_x + 25):
                self._carve(x, y, self.grass)
                
        # 3. Small Lake (let's say 5x5 approx, in top left of grass)
        lake_x = start_x + 3
        lake_y = start_y + 3
        for y in range(lake_y, lake_y + 5):
            for x in range(lake_x, lake_x + 5):
                self.world.set_cell(x, y, self.water)
                
        # 4. Small House (Walls + Door)
        house_x = start_x + 15
        house_y = start_y + 5
        house_w = 6
        house_h = 6
        
        # House Walls
        for y in range(house_y, house_y + house_h):
            for x in range(house_x, house_x + house_w):
                if x == house_x or x == house_x + house_w - 1 or y == house_y or y == house_y + house_h - 1:
                     self.world.set_cell(x, y, self.wall)
                else:
                    self.world.set_cell(x, y, self.grass) # Floor
                    
        # House Door
        # self.world.set_cell(house_x + house_w // 2, house_y + house_h - 1, self.grass) # Opening (CLOSED FOR AI TRAINING)
        
        # 5. Trapdoor (inside house)
        trapdoor_cell = Registry.get_cell("Trapdoor")
        if trapdoor_cell:
            self.world.set_cell(house_x + house_w // 2, house_y + house_h // 2, trapdoor_cell)
        else:
            print("ERROR: Trapdoor cell not found in Registry!")

        # Set spawn point for first layer (center of grass box) generally, 
        # but let's put it near the unexpected lake? Or just center. 
        # Using the rooms list format to be compatible with _init_entities in setup.py
        # Setup.py expects: spawn_room[MINX] + spawn_room[HEIGHT] // 2...
        # It treats rooms as (x, y, width, height)
        # We can fake a room for the spawn point.
        fake_spawn_room = (start_x + 10, start_y + 10, 5, 5) # Somewhere in the grass
        self.rooms.append(fake_spawn_room)

        # Add Continuous Spawner
        # Move to open field (far right of grass box)
        spawner_x = start_x + 20
        spawner_y = start_y + 10
        self.world.set_cell(spawner_x, spawner_y, self.spawner)
        
        self.world.spawn_points.append({
            'x': spawner_x,
            'y': spawner_y,
            'enemy_count': 1, # Spawn 1 Boss
            'type': "JörnBoss", # Explicit Boss type
            'spawned': False,
            'spawn_mode': 'once', # Only once
            'cooldown': 5000, 
            'last_spawn_time': 0
        })


    def _generate_dungeon(self):
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

            size = randint(1, 1 + ROOM_EXTRA_SIZE) * 2 + 1
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
                    
            # Place Spawner in center
            center_x = x + width // 2
            center_y = y + height // 2
            self.world.set_cell(center_x, center_y, self.spawner)
            
            # Add spawn metadata
            # For now picking a random enemy type - ideally we'd have a weighted list or valid set
            from core.registry import Registry # Import here to avoid circular if any
            enemy_types = [e for e in Registry.get_enemy_types() if "Boss" not in e and e != "JörnBoss"]
            
            spawn_type = "basic_enemy"
            if enemy_types:
                spawn_type = enemy_types[randint(0, len(enemy_types)-1)]
                
            self.world.spawn_points.append({
                'x': center_x, 
                'y': center_y, 
                'enemy_count': randint(2, 5), 
                'type': spawn_type,
                'spawned': False
            })

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

