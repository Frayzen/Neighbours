import math
import pygame
from core.debug import debug
from combat.weapon import Weapon
from config.settings import MAX_WEAPONS

class CombatManager:
    def __init__(self, owner):
        self.owner = owner
        self.weapons = []
        self.current_weapon_index = 0
        self.target = None
        self.last_target_check_time = 0
        self.target_check_interval = 500  # Check for target every 500ms

    @property
    def current_weapon(self):
        if not self.weapons:
            return None
        return self.weapons[self.current_weapon_index]

    def add_weapon(self, weapon: Weapon):
        if len(self.weapons) < MAX_WEAPONS:
            self.weapons.append(weapon)
            debug.log(f"Added {weapon.name} to inventory")
        else:
            debug.log(f"Inventory full! Cannot add {weapon.name}")

    def switch_weapon(self):
        if not self.weapons:
            return
        self.current_weapon_index = (self.current_weapon_index + 1) % len(self.weapons)
        debug.log(f"Switched to {self.current_weapon.name}")

    def update(self, enemies, current_time):
        if not self.current_weapon:
            return

        # Auto-Targeting Logic (not every frame)
        if current_time - self.last_target_check_time > self.target_check_interval:
            self.target = self.find_nearest_target(enemies)
            self.last_target_check_time = current_time

        # Auto-Attacking Logic
        if self.target:
            # Check if target is still alive/valid (if enemies list changes)
            if self.target not in enemies:
                self.target = None
                return

            distance = self.get_distance_to(self.target)
            if distance <= self.current_weapon.range:
                if self.current_weapon.can_attack(current_time):
                    self.attack(self.target, enemies, current_time)
            else:
                # If target is out of range clear target
                pass

    def find_nearest_target(self, enemies):
        nearest_enemy = None
        min_distance = float('inf')

        for enemy in enemies:
            distance = self.get_distance_to(enemy)
            if distance < min_distance:
                min_distance = distance
                nearest_enemy = enemy
        
        return nearest_enemy

    def get_distance_to(self, target):
        dx = self.owner.x - target.x
        dy = self.owner.y - target.y
        return math.sqrt(dx * dx + dy * dy)

    def attack(self, target, enemies, current_time):
        self.current_weapon.attack(current_time, owner=self.owner, target=target, enemies=enemies)
        
        targets_hit = self.current_weapon.get_targets(target, enemies)
        
        for hit_target in targets_hit:
            # debug.log(f"Hit enemy with {self.current_weapon.name} for {self.current_weapon.damage} damage!")
            if hasattr(hit_target, 'take_damage'):
                hit_target.take_damage(self.current_weapon.damage)
