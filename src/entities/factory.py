from entities.enemies.enemy import Enemy
from entities.enemies.boss import Boss
from entities.enemies.healer import Healer
from entities.enemies.ranged import RangedEnemy
from core.registry import Registry
"""Lara KHREIS"""

def create_enemy(game, x, y, enemy_type="basic_enemy", modifiers=None):
    """
    Factory function to create the appropriate Enemy subclass based on type/behavior.
    """
    if enemy_type == "JoernBoss":
        return Boss(game, x, y, enemy_type, modifiers)
    
    config = Registry.get_enemy_config(enemy_type)
    behavior = "melee"
    if config:
        behavior = config.get("behavior", "melee")
        
    if behavior == "healer":
        return Healer(game, x, y, enemy_type, modifiers)
    elif behavior == "ranged":
        return RangedEnemy(game, x, y, enemy_type, modifiers)
    else:
        return Enemy(game, x, y, enemy_type, modifiers)
