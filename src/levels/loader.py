from config.settings import GRID_HEIGHT, GRID_WIDTH, MAZE_SCALE_UP, ROOM_AMOUNT, ROOM_EXTRA_SIZE, ROOM_MIN_SIZE
from core.registry import Registry
from random import randint
from core.world import World
from typing import List, Tuple

"""Janis REISENAUER"""

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
        self.ground = Registry.get_cell("Ground")
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
            cell_type = self.ground if self.ground else self.grass
        self.world.set_cell(x, y, cell_type)
        self.regions[y][x] = self.current_region

    # -------------------------------------------------------------------------
    # MAIN GENERATOR
    # -------------------------------------------------------------------------
    def generate(self, config):
        if config is None:
            # Fallback legacy
            return self._generate_dungeon()

        self.world = World() # Reset world for new layer
        
        # Override world dimensions if provided
        if "width" in config and "height" in config:
            self.world = World(width=config["width"], height=config["height"])
        
        # Reset regions
        self.regions = [[None for _ in range(self.world.width)]
                        for _ in range(self.world.height)]
        self.current_region = -1
        self.rooms = [] # Reset rooms
        
        level_type = config.get("type", "dungeon")
        
        if level_type == "file":
             self._load_from_json(config.get("path"))
        elif level_type == "dungeon":
             self._generate_dungeon(config)
        else:
             print(f"Unknown level type: {level_type}")
             self._generate_dungeon() # Fallback

        self.world.scale(MAZE_SCALE_UP)
        
        # Scale rooms if present (dungeons)
        for i in range(len(self.rooms)):
            x, y, w, h =  self.rooms[i]
            self.rooms[i] = (x * MAZE_SCALE_UP, y * MAZE_SCALE_UP, w * MAZE_SCALE_UP, h * MAZE_SCALE_UP)

        return self.world

    def _load_from_json(self, path):
        import json
        import os
        from config.settings import BASE_DIR
        
        # Construct full path (relative to src/ generally)
        # config paths were like "config/levels/spawn.json"
        full_path = os.path.join(BASE_DIR, path)
        if not os.path.exists(full_path):
             # Try relative to src if needed, but BASE_DIR should be right
             print(f"ERROR: Level file not found at {full_path}")
             return

        try:
            with open(full_path, 'r') as f:
                data = json.load(f)
            
            # Dimensions are likely handled in generate() but let's ensure
            if "width" in data and "height" in data:
                 w, h = data["width"], data["height"]
                 if w != self.world.width or h != self.world.height:
                     print(f"DEBUG: Resizing world to {w}x{h} based on JSON file.")
                     self.world = World(width=w, height=h)
                     # Reset regions for new size
                     self.regions = [[None for _ in range(self.world.width)]
                                     for _ in range(self.world.height)]

            # Legend mapping
            legend = data.get("legend", {})
            layout = data.get("layout", [])
            
            # Map legend keys to Cell objects
            cell_map = {}
            for key, val in legend.items():
                cell = Registry.get_cell(val)
                if not cell:
                    print(f"Warning: Cell '{val}' not found in Registry.")
                    cell = self.wall # Fallback
                cell_map[key] = cell
            
            # Fill World
            start_y = 0
            for row_idx, line in enumerate(layout):
                if row_idx >= self.world.height: break
                for col_idx, char in enumerate(line):
                     if col_idx >= self.world.width: break
                     
                     cell = cell_map.get(char, self.wall)
                     self.world.set_cell(col_idx, row_idx, cell)
            
            # Handle Spawn Point (Fake room for setup.py compatibility)
            spawn_pt = data.get("spawn_point")
            if spawn_pt:
                # Add a 1x1 room at spawn for logic that needs it
                # Using 5x5 just to be safe with spiral search logic
                sx, sy = spawn_pt.get("x", 1), spawn_pt.get("y", 1)
                self.rooms.append((sx, sy, 1, 1)) 
            else:
                 self.rooms.append((1, 1, 1, 1))

            # Handle Spawners (Entities)
            # Add them to world.spawn_points
            spawners = data.get("spawners", [])
            for sp in spawners:
                # Convert to world coordinates (pre-scale)
                # But spawn_points expect POST-SCALE coordinates usually?
                # Looking at _generate_overworld original: 
                # spawner_x * MAZE_SCALE_UP
                
                # So we store them as pre-scale here, but valid format?
                # world.spawn_points entry:
                # 'x': spawner_x * MAZE_SCALE_UP
                
                self.world.spawn_points.append({
                    'x': sp.get('x') * MAZE_SCALE_UP,
                    'y': sp.get('y') * MAZE_SCALE_UP,
                    'enemy_count': sp.get('enemy_count', 1),
                    'type': sp.get('type', 'basic_enemy'),
                    'spawned': sp.get('spawned', False),
                    'spawn_mode': sp.get('spawn_mode', 'once'),
                    'cooldown': sp.get('cooldown', 5000),
                    'last_spawn_time': 0
                })
                
                # Visual placement of spawner if needed? 
                # Usually invisible or under floor, but if legend had 'B' for spawner, we might have placed a 'Spawner' cell already.
                
        except Exception as e:
            print(f"Failed to load level JSON: {e}")


    def _generate_dungeon(self, config=None):
        # Fill background with wall
        for y in range(self.world.height):
            for x in range(self.world.width):
                self.world.set_cell(x, y, self.wall)

        self.__generate_rooms()

        # Fill unused space with mazes
        for x in range(1, self.world.width, 2):
            for y in range(1, self.world.height, 2):
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

            size = randint(ROOM_MIN_SIZE, ROOM_MIN_SIZE + ROOM_EXTRA_SIZE) * 2 + 1
            width = size
            height = size

            rectangularity = randint(0, 1 + size // 2) * 2
            if randint(0, 1) == 0:
                width += rectangularity
            else:
                height += rectangularity

            x = randint(0, (self.world.width - width) // 2) * 2 + 1
            y = randint(0, (self.world.height - height) // 2) * 2 + 1
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
            # self.world.set_cell(center_x, center_y, self.spawner) # REMOVED: Prevent visual grid artifact (2x2 purple blocks). We use Entities now.
            
            # Using Spawner Entity Concept now
            # We don't add to world.spawn_points anymore, but we need to tell Game to create Spawners
            # The Loader mainly builds the static World. The GameSetup or GameLogic handles Entities.
            # However, the loader generates the structure.
            # Let's attach the spawner data to the world, so setup can instantiate them?
            # OR if we have access to 'game' here? We don't.
            # We can store "spawner_locations" in world and let setup create them.
            
            # Reusing spawn_points list but storing just location for Spawner Entity creation
            self.world.spawn_points.append({
                'x': center_x * MAZE_SCALE_UP, 
                'y': center_y * MAZE_SCALE_UP,
                'type': 'spawner_entity' # Marker for setup
            })

        # GUARANTEED TRAPDOOR in the LAST room generated
        if self.rooms:
            last_room = self.rooms[-1]
            lx, ly, lw, lh = last_room
            
            # Center of last room
            tx = lx + lw // 2
            ty = ly + lh // 2
            
            # Place Trapdoor Cell
            trapdoor = Registry.get_cell("Trapdoor")
            if trapdoor:
                self.world.set_cell(tx, ty, trapdoor)
                print(f"DEBUG: Placed Guaranteed Trapdoor at ({tx}, {ty})")
                
                # Remove any spawner at this exact location to avoid stacking
                # We placed a spawner at center_x, center_y for every room above
                # So we just need to remove the last entry in self.world.spawn_points?
                # The loop ends, so the last append corresponds to the last room.
                if self.world.spawn_points:
                    self.world.spawn_points.pop()
                    print("DEBUG: Removed conflicting spawner for Trapdoor.")
            else:
                print("ERROR: Trapdoor cell not found!")

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
                # Door
                # self.world.set_cell(x, y, self.door) # REMOVED: Replaced with Entity to avoid 2x2 tiling
                fill_cell = self.ground if self.ground else self.grass
                self.world.set_cell(x, y, fill_cell)
                
                # Add Door Entity marker
                # Note: Center of the junction. 
                # Spawn points list stores keys for setup.py
                self.world.spawn_points.append({
                    'x': x * MAZE_SCALE_UP,
                    'y': y * MAZE_SCALE_UP,
                    'type': 'door'
                })
            else:
                fill_cell = self.ground if self.ground else self.grass
                self.world.set_cell(x, y, fill_cell)
        else:
            # Mostly closed doors
            # self.world.set_cell(x, y, self.door) # REMOVED
            fill_cell = self.ground if self.ground else self.grass
            self.world.set_cell(x, y, fill_cell)
            self.world.spawn_points.append({
                'x': x * MAZE_SCALE_UP,
                'y': y * MAZE_SCALE_UP,
                'type': 'door'
            })

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

