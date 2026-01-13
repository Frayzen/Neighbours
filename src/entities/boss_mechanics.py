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
    SUMMON_POOL = ["basic_enemy", "fast_enemy", "ranger"]
    
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

def perform_bullet_hell(boss, game):
    """
    Phase 3: 360 shots.
    """
    from entities.projectile import Projectile
    
    num_projectiles = 18
    angle_step = 360 / num_projectiles
    
    for i in range(num_projectiles):
        angle_deg = i * angle_step
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
            color=(255, 0, 0)
        )
        game.projectiles.append(proj)
        
    debug.log("JörnBoss BULLET HELL!")
