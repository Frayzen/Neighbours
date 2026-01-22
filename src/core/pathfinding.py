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

def find_path(start_x, start_y, target_x, target_y, world):
    """
    A* Pathfinding implementation.
    Returns a list of (x, y) tuples in WORLD COORDINATES (pixels) representing the path.
    """
    # Grid coordinates
    sx, sy = int(start_x // CELL_SIZE), int(start_y // CELL_SIZE)
    tx, ty = int(target_x // CELL_SIZE), int(target_y // CELL_SIZE)
    
    cols = world.width
    rows = world.height
    
    # Heuristic: Manhattan distance
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    frontier = []
    heapq.heappush(frontier, (0, (sx, sy)))
    came_from = {}
    cost_so_far = {}
    came_from[(sx, sy)] = None
    cost_so_far[(sx, sy)] = 0
    
    found = False
    
    while frontier:
        _, current = heapq.heappop(frontier)
        
        if current == (tx, ty):
            found = True
            break
        
        # Neighbors: Up, Down, Left, Right
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx, ny = current[0] + dx, current[1] + dy
            
            if 0 <= nx < cols and 0 <= ny < rows:
                cell = world.get_cell(nx, ny)
                if cell and not cell.walkable:
                     continue
                
                new_cost = cost_so_far[current] + 1
                if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                    cost_so_far[(nx, ny)] = new_cost
                    priority = new_cost + heuristic((nx, ny), (tx, ty))
                    heapq.heappush(frontier, (priority, (nx, ny)))
                    came_from[(nx, ny)] = current
                    
    if found:
        # Reconstruct path
        path = []
        curr = (tx, ty)
        while curr != (sx, sy):
            # Center of the cell in world coords
            wx = curr[0] * CELL_SIZE + CELL_SIZE // 2
            wy = curr[1] * CELL_SIZE + CELL_SIZE // 2
            path.append((wx, wy))
            curr = came_from[curr]
            
        path.append((sx * CELL_SIZE + CELL_SIZE // 2, sy * CELL_SIZE + CELL_SIZE // 2))
        path.reverse()
        return path
    
    return []
