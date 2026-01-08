import heapq
import math
from config.settings import CELL_SIZE

class FlowField:
    def __init__(self):
        self.vector_field = {}
        self.distance_field = {}
        self.cols = 0
        self.rows = 0

    def update(self, target_x, target_y, world):
        self.cols = world.width
        self.rows = world.height
        
        # Convert target world pos to grid pos
        target_grid_x = int(target_x / CELL_SIZE)
        target_grid_y = int(target_y / CELL_SIZE)
        
        # 1. Integration Field (Dijkstra/BFS)
        # Initialize distance grid with infinity
        self.distance_field = {} # Reset
        
        queue = []
        
        # Add target to queue
        start_node = (target_grid_x, target_grid_y)
        self.distance_field[start_node] = 0
        heapq.heappush(queue, (0, start_node))
        
        # Directions: Up, Down, Left, Right
        neighbors = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        while queue:
            dist, current = heapq.heappop(queue)
            cx, cy = current
            
            if dist > self.distance_field.get(current, float('inf')):
                continue
            
            for dx, dy in neighbors:
                nx, ny = cx + dx, cy + dy
                
                # Check bounds
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    # Check walkability
                    # world.get_cell_full returns (cell, offset), we just need the cell properties
                    # Assuming we can get simple cell info or use get_cell_full
                    # If world has get_cell(x, y) that returns just the cell, that's better.
                    # I'll rely on reading world.py before finalizing this, but assuming get_cell_full logic:
                    cell_data = world.get_cell_full(nx, ny)
                    if cell_data:
                        cell, _ = cell_data
                        if not cell.walkable:
                            continue
                            
                    new_dist = dist + 1
                    if new_dist < self.distance_field.get((nx, ny), float('inf')):
                        self.distance_field[(nx, ny)] = new_dist
                        heapq.heappush(queue, (new_dist, (nx, ny)))
                        
        # 2. Vector Field
        self.vector_field = {}
        for x in range(self.cols):
            for y in range(self.rows):
                if (x, y) in self.distance_field:
                    min_dist = self.distance_field[(x, y)]
                    best_dir = (0, 0)
                    
                    # If we are at the target, vector is (0,0) (or maybe towards precise center?)
                    if min_dist == 0:
                        self.vector_field[(x, y)] = (0, 0)
                        continue
                        
                    for dx, dy in neighbors:
                        nx, ny = x + dx, y + dy
                        if (nx, ny) in self.distance_field:
                            dist = self.distance_field[(nx, ny)]
                            if dist < min_dist:
                                min_dist = dist
                                best_dir = (dx, dy)
                    
                    self.vector_field[(x, y)] = best_dir
                else:
                    # Unreachable
                    self.vector_field[(x, y)] = (0, 0)

    def get_vector(self, x, y):
        # x, y are world coordinates
        grid_x = int(x / CELL_SIZE)
        grid_y = int(y / CELL_SIZE)
        
        return self.vector_field.get((grid_x, grid_y), (0, 0))

    def get_distance(self, x, y):
         grid_x = int(x / CELL_SIZE)
         grid_y = int(y / CELL_SIZE)
         return self.distance_field.get((grid_x, grid_y), float('inf'))
