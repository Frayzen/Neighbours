import pygame
import random
import math
from core.debug import debug
from config.settings import CELL_SIZE

# Ability Cooldowns (ms)
COOLDOWN_GRAVITY = 5000
COOLDOWN_SUMMON = 10000
COOLDOWN_DASH = 8000
COOLDOWN_SHIELD = 15000
COOLDOWN_BULLET_HELL = 6000

# Other constants
SHIELD_DURATION = 3000
DASH_DURATION = 500
DASH_SPEED_MULTIPLIER = 10

def perform_gravity_smash(boss, player):
    # Smooth Gravity Smash (Pull)
    dx = boss.x - player.x
    dy = boss.y - player.y
    dist = (dx**2 + dy**2)**0.5
    
    if dist > 0:
        # Normalize
        ndx = dx / dist
        ndy = dy / dist
        
        player.external_force[0] = ndx * 50 # Pull 50 pixels?
        player.external_force[1] = ndy * 50
        
        debug.log("JörnBoss used Gravity Smash!")

def perform_summon(boss, game, enemy_type=None, count=None):
    """
    Phase 1: Spawn minions.
    If enemy_type is None, picks random from pool.
    """
    if count is None:
        count = random.randint(2, 3)
        
    # Pool of summonable minions
    SUMMON_POOL = ["basic_enemy", "fast_enemy", "ranger", "tank_enemy", "healer"]
    
    from entities.enemy import Enemy
    
    for _ in range(count):
        # Choose type
        etype = enemy_type if enemy_type else random.choice(SUMMON_POOL)
        
        # Random pos around boss
        angle = random.uniform(0, 6.28)
        radius = random.randint(50, 100)
        spawn_x = boss.x + math.cos(angle) * radius
        spawn_y = boss.y + math.sin(angle) * radius
        
        # Check bounds/walls? Assuming okay for now or handled by collision resolution later
        # Verify if enemy type exists to avoid crashes? The Enemy class handles fallback but warned.
        
        minion = Enemy(game, spawn_x, spawn_y, etype)
        game.gridObjects.append(minion)
        
    debug.log(f"JörnBoss summoned {count} {enemy_type if enemy_type else 'random'} minions!")

def perform_dash(boss, player):
    """
    Phase 2: Dash behind player.
    """
    # Teleport/Dash logic
    # "Setze Bewegungsvektor direkt auf die Rückseite des Spielers"
    
    # Let's calculate a target point behind the player
    # Assume "behind" is opposite to player's facing? Or just opposite to boss?
    # Let's simple go to the opposite side of the player relative to current boss pos
    
    dx = player.x - boss.x
    dy = player.y - boss.y
    dist = math.sqrt(dx*dx + dy*dy)
    
    if dist > 0:
        # Vector Boss -> Player
        dir_x = dx / dist
        dir_y = dy / dist
        
        # Target: Player Pos + (Vector * 50)
        target_x = player.x + dir_x * 50
        target_y = player.y + dir_y * 50
        
        # For simple dash implementation: Teleport for now, or high speed move?
        # Prompt: "Erhöhe boss.speed für 0.5s drastisch... Setze Bewegungsvektor"
        # We can simulate the dash by setting a dash timer in boss and overriding movement
        
        boss.dash_timer = pygame.time.get_ticks()
        boss.dash_target = (target_x, target_y)
        boss.is_dashing = True
        
        debug.log("JörnBoss Dashing!")

def activate_shield(boss):
    """
    Phase 3: Shield.
    """
    boss.is_shielded = True
    boss.shield_timer = pygame.time.get_ticks()
    boss.color = (0, 0, 255) # Blue shield visual
    debug.log("JörnBoss Shield Activated!")

def perform_firebreath(boss, game, player):
    """
    Firebreath: Stream of fireballs towards player with random angle spread.
    """
    from entities.projectile import Projectile
    
    NUM_PROJECTILES = 30
    CONE_ANGLE = 45 # Degrees spread (+/- 22.5)
    
    # Calculate base direction to player
    dx = player.x - boss.x
    dy = player.y - boss.y
    base_angle = math.degrees(math.atan2(dy, dx))
    
    debug.log("JörnBoss uses FIREBREATH!")
    
    for _ in range(NUM_PROJECTILES):
        # Random offset angle
        offset = random.uniform(-CONE_ANGLE/2, CONE_ANGLE/2)
        angle_deg = base_angle + offset
        angle_rad = math.radians(angle_deg)
        
        p_dx = math.cos(angle_rad)
        p_dy = math.sin(angle_rad)
        
        # Random speed variation
        speed = random.uniform(4, 7)
        
        # Random delay for stream effect (0 to 1 second)
        # 60 frames = 1 sec approx
        delay = random.randint(0, 60)
        
        proj = Projectile(
            boss.x + boss.w*CELL_SIZE/2, 
            boss.y + boss.h*CELL_SIZE/2,
            direction=(p_dx, p_dy),
            speed=speed,
            damage=12,
            owner_type="enemy",
            visual_type="FIREBALL",
            color=(255, 100, 0),
            start_delay=delay
        )
        game.projectiles.append(proj)

def perform_powerful_fireball(boss, game, player):
    """
    Single massive fireball. Slow, high damage, explodes on impact.
    """
    from entities.projectile import Projectile
    
    # Calculate direction (Still useful for initial direction if needed, but TARGET_EXPLOSION uses target_pos)
    # We pass target_pos to Projectile
    
    target_pos = (player.x + player.w*CELL_SIZE/2, player.y + player.h*CELL_SIZE/2)
    
    proj = Projectile(
        boss.x + boss.w*CELL_SIZE/2, 
        boss.y + boss.h*CELL_SIZE/2,
        direction=None, # Will be calculated by update based on target
        speed=4, 
        damage=50, 
        owner_type="enemy",
        behavior="TARGET_EXPLOSION",
        visual_type="METEOR", 
        target_pos=target_pos,
        color=(139, 0, 0), 
        explode_radius=3 * CELL_SIZE # Explodes in 3 tile radius (logic.py expects pixels for radius? No, wait.)
        # Logic.py: vfx_manager.add_effect(..., radius=proj.explode_radius)
        # Logic.py damage: if dist_sq <= proj.explode_radius ** 2
        # So explode_radius should be in pixels!
        # 3 tiles = 3 * CELL_SIZE
    )
    game.projectiles.append(proj)
    debug.log("JörnBoss casts METEOR at coordinates!")
def perform_bullet_hell(boss, game):
    """
    Phase 3: 360 shots.
    """
    from entities.projectile import Projectile
    
    num_rings = 4
    num_projectiles_per_ring = 18
    angle_step = 360 / num_projectiles_per_ring
    
    # Delays in "frames" (assuming update is called ~60 times a sec, or at least regularly)
    DELAY_PER_RING = 30 # 0.5 seconds approx

    for ring in range(num_rings):
        # Rotation offset for this ring
        angle_offset = ring * 15 # 15 degrees shift per ring
        
        # Delay for this ring
        ring_delay = ring * DELAY_PER_RING
        
        for i in range(num_projectiles_per_ring):
            angle_deg = i * angle_step + angle_offset
            angle_rad = math.radians(angle_deg)
            
            dx = math.cos(angle_rad)
            dy = math.sin(angle_rad)
            
            proj = Projectile(
                boss.x + boss.w*CELL_SIZE/2, 
                boss.y + boss.h*CELL_SIZE/2,
                direction=(dx, dy),
                speed=5,
                damage=15,
                owner_type="enemy",
                visual_type="FIREBALL", # Or any boss projectile
                color=(255, 0, 0),
                start_delay=ring_delay
            )
            game.projectiles.append(proj)
            
    debug.log(f"JörnBoss BULLET HELL! ({num_rings} rings)")

def perform_The_Final_Ember(boss, game):
    """
    Perform the final Ember attack on phase switch from 2 to 3.
    Set random World tiles on fire.
    """
    from entities.hazard import FireHazard
    
    # Configuration
    NUM_FIRES = 20 
    DURATION_MIN = 5000
    DURATION_MAX = 10000
    DAMAGE = 10
    
    debug.log("JörnBoss unleashes THE FINAL EMBER!")
    
    debug.log("JörnBoss unleashes THE FINAL EMBER!")
    
    # Optimization: Spawn fires only near the boss
    # Rejection sampling is faster than scanning the whole map
    RADIUS = 15 # Tiles radius
    boss_gx = int(boss.x / CELL_SIZE)
    boss_gy = int(boss.y / CELL_SIZE)
    
    spawned_count = 0
    max_attempts = NUM_FIRES * 5 # Allow some failures
    
    for _ in range(max_attempts):
        if spawned_count >= NUM_FIRES:
            break
            
        # Random offset within radius
        off_x = random.randint(-RADIUS, RADIUS)
        off_y = random.randint(-RADIUS, RADIUS)
        
        tx = boss_gx + off_x
        ty = boss_gy + off_y
        
        # Check bounds
        if 0 <= tx < game.world.width and 0 <= ty < game.world.height:
            cell = game.world.get_cell(tx, ty)
            if cell and cell.walkable:
                # Convert grid to pixels
                px = tx * CELL_SIZE
                py = ty * CELL_SIZE
                
                # Create Hazard
                fire = FireHazard(px, py, DURATION_MIN, DURATION_MAX, DAMAGE, game)
                game.gridObjects.append(fire)
                spawned_count += 1
                
    debug.log(f"Ignited {spawned_count} tiles near JörnBoss with Final Ember.")
