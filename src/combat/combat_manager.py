import math
import pygame
from core.debug import debug
from combat.weapon import Weapon
from combat.weapon import Weapon
from config.settings import MAX_WEAPONS, TARGET_CHECK_INTERVAL
from config.constants import OP_ADD, OP_MULTIPLY

class CombatManager:
    def __init__(self, owner):
        self.owner = owner
        self.weapons = []
        self.current_weapon_index = 0
        self.target = None
        self.last_target_check_time = 0
        self.target_check_interval = TARGET_CHECK_INTERVAL  # Check for target every 500ms

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

    def apply_upgrade(self, item):
        target_name = getattr(item, 'target_weapon', None)
        target_tag = getattr(item, 'target_tag', None)
        
        # Handle dict access for safety
        if isinstance(item, dict):
             if not target_name: target_name = item.get('target_weapon')
             if not target_tag: target_tag = item.get('target_tag')
        
        # Handle object access if attribute missing from dict approach above
        if hasattr(item, 'target_weapon'): target_name = item.target_weapon
        if hasattr(item, 'target_tag'): target_tag = item.target_tag

        if not target_name and not target_tag:
            debug.log(f"Upgrade {item.name} has no target weapon or tag specified.")
            return

        upgraded_count = 0
        for weapon in self.weapons:
            # Check if weapon matches target_name OR matches target_tag
            matches_id = (target_name and weapon.id == target_name)
            matches_tag = (target_tag and target_tag in weapon.tags)
            
            if matches_id or matches_tag:
                debug.log(f"Upgrading {weapon.name} (ID: {weapon.id}) with {item.name}")
                for effect, data in item.effects.items():
                    op = data["op"]
                    val = data["value"]
                    
                    if hasattr(weapon, effect):
                        current_val = getattr(weapon, effect)
                        if op == OP_ADD:
                            setattr(weapon, effect, current_val + val)
                        elif op == OP_MULTIPLY:
                            setattr(weapon, effect, current_val * (1 + val))
                            
                        debug.log(f"  -> {effect} modified (Op: {op}, Val: {val}). New: {getattr(weapon, effect)}")
                    if hasattr(weapon, effect):
                        current_val = getattr(weapon, effect)
                        if op == OP_ADD:
                            setattr(weapon, effect, current_val + val)
                        elif op == OP_MULTIPLY:
                            setattr(weapon, effect, current_val * (1 + val))
                            
                        debug.log(f"  -> {effect} modified (Op: {op}, Val: {val}). New: {getattr(weapon, effect)}")
                    else:
                        debug.log(f"  -> Weapon has no attribute '{effect}'")
                upgraded_count += 1
        
        if upgraded_count == 0:
            debug.log(f"Target weapon {target_name} or tag {target_tag} not found in inventory.")

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
                damage = self.current_weapon.damage * self.owner.damage_mult
                hit_target.take_damage(damage)
