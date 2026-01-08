import heapq
import math
from config.settings import CELL_SIZE

class FlowField:
    def __init__(self):
        self.vector_field = {}
        self.distance_field = {}
        self.cols = 0
        self.rows = 0

    def update(self, target_x, target_y, world, max_dist=None):
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
        
        # Directions: Up, Down, Left, Right + Diagonals
        # (dx, dy, cost)
        neighbors = [
            (0, -1, 1), (0, 1, 1), (-1, 0, 1), (1, 0, 1),
            (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)
        ]
        
        while queue:
            dist, current = heapq.heappop(queue)
            cx, cy = current
            
            if dist > self.distance_field.get(current, float('inf')):
                continue
            
            if max_dist is not None and dist > max_dist:
                continue

            for dx, dy, cost in neighbors:
                nx, ny = cx + dx, cy + dy
                
                # Check bounds
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    cell_data = world.get_cell_full(nx, ny)
                    if cell_data:
                        cell, _ = cell_data
                        if not cell.walkable:
                            continue
                            
                    new_dist = dist + cost
                    
                    if max_dist is not None and new_dist > max_dist:
                        continue

                    if new_dist < self.distance_field.get((nx, ny), float('inf')):
                        self.distance_field[(nx, ny)] = new_dist
                        heapq.heappush(queue, (new_dist, (nx, ny)))
                        
        # 2. Vector Field
        # Optimization: Only iterate over cells explicitly found in distance_field
        self.vector_field = {}
        
        for (x, y), min_dist in self.distance_field.items():
            if min_dist == 0:
                self.vector_field[(x, y)] = (0, 0)
                continue
                
            # Check all 8 neighbors for steep descent
            best_dir = (0, 0)
            target_neighbor_dist = min_dist
            found_better = False
            
            for dx, dy, cost in neighbors:
                nx, ny = x + dx, y + dy
                if (nx, ny) in self.distance_field:
                    dist = self.distance_field[(nx, ny)]
                    if dist < target_neighbor_dist:
                        target_neighbor_dist = dist
                        best_dir = (dx, dy)
                        found_better = True
            
            if found_better:
                # Normalize vector for smooth movement
                mag = math.sqrt(best_dir[0]**2 + best_dir[1]**2)
                if mag > 0:
                    self.vector_field[(x, y)] = (best_dir[0]/mag, best_dir[1]/mag)
                else:
                    self.vector_field[(x, y)] = (0,0)
            else:
                 self.vector_field[(x, y)] = (0,0)

    def get_vector(self, x, y):
        # x, y are world coordinates
        grid_x = int(x / CELL_SIZE)
        grid_y = int(y / CELL_SIZE)
        
        return self.vector_field.get((grid_x, grid_y), (0, 0))

    def get_distance(self, x, y):
         grid_x = int(x / CELL_SIZE)
         grid_y = int(y / CELL_SIZE)
         return self.distance_field.get((grid_x, grid_y), float('inf'))
