```mermaid
classDiagram
    %% ==================================================
    %% 1. CORE SYSTEM (The Engine & Orchestration)
    %% ==================================================
    class Game {
        +Player player
        +list gridObjects
        +list enemies
        +GameRenderer renderer
        +GameLogic logic
        +Camera camera
        +World world
        +DamageTexts damage_texts
        +bool paused
        +run()
        +restart_game()
    }

    class GameLogic {
        +Game game
        +update()
        +handle_event(event)
        +handle_pause_input(event)
        -_handle_player_movement()
        -_handle_combat()
        -_handle_pickups()
        -_handle_spawning_and_drops()
    }

    class GameRenderer {
        +Surface rendering_surface
        +Surface background_world
        +draw(camera)
        +draw_pause_menu()
        -_draw_ui()
        -_draw_entities()
        -_draw_world()
    }

    class SaveManager {
        <<Static>>
        +SAVE_FILE_PATH: str$
        +save_game(game)$
        +load_game(game)$
        +has_save_file()$ bool
        +delete_save_file()$
    }

    class Registry {
        <<Static>>
        -_cells: dict$
        -_enemies: dict$
        +load_cells(path)$
        +load_enemies(path)$
        +get_cell(name)$ Cell
        +get_enemy_config(name)$ dict
    }

    class Camera {
        +float x
        +float y
        +update(player)
        +get_subregion() Rect
    }

    %% ==================================================
    %% 2. ENTITIES (The Actors)
    %% ==================================================
    class GridObject {
        <<Abstract>>
        +float x
        +float y
        +float w
        +float h
        +tuple color
        +draw(screen)
        +update(target_pos)
    }

    class Player {
        +Game game
        +CombatManager combat
        +int health, max_health
        +int xp, level, xp_to_next_level
        +float speed_mult, damage_mult
        +list active_effects
        +move(keys, world)
        +collect_item(item)
        +gain_xp(amount)
        +take_damage(amount)
        -modify_stat(effect, op, value, revert)
    }

    class Enemy {
        +string enemy_type
        +float speed
        +int health, damage
        +Surface texture
        +take_damage(amount)
        +die()
        +update(target_pos)
    }

    class XPOrb {
        +int value
        +Vector2 velocity
        +move_towards(tx, ty)
        +draw(surface)
    }

    %% ==================================================
    %% 3. COMBAT & WEAPONS (The Mechanics)
    %% ==================================================
    class CombatManager {
        +Player owner
        +list weapons
        +Weapon current_weapon
        +update(enemies, time)
        +apply_upgrade(item)
        +attack(target, enemies, time)
    }

    class Weapon {
        +string id, name
        +int damage, cooldown
        +float range, aoe_radius
        +list tags
        +Surface image
        +function behavior_func
        +can_attack(time) bool
    }

    class WeaponFactory {
        <<Static>>
        -_weapons_data: dict$
        +load_weapons()$
        +create_weapon(weapon_id)$ Weapon
    }

    %% ==================================================
    %% 4. LEVELS & 5. WORLD (Generation & Environment)
    %% ==================================================
    class WorldLoader {
        +World world
        +list rooms
        +generate() World
        -growMaze(x, y)
        -generate_rooms()
        -connect_regions()
    }

    class World {
        +int width, height
        +list grid
        +set_cell(x, y, cell)
        +get_cell(x, y) Cell
        +get_cell_full(x, y) tuple
    }

    class Cell {
        +string name
        +bool walkable
        +Surface texture
        +string trigger
    }

    %% ==================================================
    %% 6. ITEMS (The Loot)
    %% ==================================================
    class Item {
        +string name, type, rarity
        +dict effects
        +int duration
        +Surface image
        +move_towards(tx, ty)
    }

    class ItemFactory {
        <<Static>>
        -_items: list$
        +load_items()$
        +create_random_item(x, y, luck)$ Item
    }

    %% ==================================================
    %% RELATIONSHIPS
    %% ==================================================
    
    %% Core Orchestration
    Game "1" *-- "1" GameLogic : processes logic
    Game "1" *-- "1" GameRenderer : handles visuals
    Game "1" *-- "1" World : manages grid
    Game "1" *-- "1" Camera : manages view
    Game ..> SaveManager : uses for persistence$
    Game ..> Registry : retrieves configs$

    %% Inheritance
    GridObject <|-- Player
    GridObject <|-- Enemy
    GridObject <|-- Item
    GridObject <|-- XPOrb

    %% Bidirectional Link
    Game "1" -- "1" Player : manages < > references

    %% Combat & Progression
    Player "1" *-- "1" CombatManager : delegates combat
    CombatManager "1" o-- "*" Weapon : manages inventory
    WeaponFactory ..> Weapon : creates$
    
    %% Generation
    WorldLoader ..> World : populates
    WorldLoader ..> Registry : uses for cell archetypes$
    World "1" *-- "*" Cell : composed of

    %% Loot
    ItemFactory ..> Item : creates$
    ```
