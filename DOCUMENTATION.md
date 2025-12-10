# Neighbours - Project Documentation

## Features

### 1. World & Environments

- **Grid System**: The game operates on a 32x32 grid.
- **Environment Types**: Tiles are defined in `src/config/environments.json`.
  - Properties: `walkable`, `texture_path`, `color`, `width`, `height`, `trigger`.
  - Supports multi-tile objects (e.g., a 1x2 Door).
- **Registry**: A central registry loads and manages environment definitions, allowing for easy addition of new tile types without changing code.
- **Rendering**:
  - Supports textures (PNG images).
  - Falls back to solid colors if textures are missing.
  - Automatically centers the map on the screen.

### 2. Player

- **Movement**: Smooth movement using WASD or Arrow keys.
- **Collision Detection**:
  - **Map Bounds**: Player cannot walk off the grid.
  - **Environment**: Player collides with non-walkable tiles (Walls, Water, etc.).
  - **Sliding**: Collision logic allows sliding along walls for better game feel.
- **Interaction**: Player triggers events when colliding with specific objects (e.g., Doors).

### 3. Entities (Enemies)

- **Spawning**: Press `SPACE` to spawn an enemy at a random location within the map bounds.
- **AI**: Enemies simply follow the player's current position.
- **Rendering**: Enemies are rendered as red squares matching the grid tile size.

### 4. Level System

- **Loader**: Levels are loaded via `src/levels/loader.py`.
- **Level 1**: Includes a grass field, boundary walls, a water pond, and a door.

### 5. Debugging

- **Overlay**: A debug overlay displays temporary messages in the top-left corner of the screen.
- **Usage**: Used to show trigger events (e.g., "Door triggered!").

## Project Structure

```
src/
├── assets/             # Game assets
│   └── images/         # Texture files (e.g., Grass.Png)
├── config/             # Configuration files
│   ├── environments.json # Tile definitions
│   └── settings.py     # Constants (Screen size, etc.)
├── core/               # Core engine logic
│   ├── debug.py        # Debug overlay system
│   ├── game.py         # Main Game loop and initialization
│   ├── registry.py     # Environment loader
│   ├── triggers.py     # Trigger function definitions
│   └── world.py        # World and Environment classes
├── entities/           # Game objects
│   ├── base.py         # Base GridObject class
│   ├── enemy.py        # Enemy logic
│   └── player.py       # Player movement and collision
├── levels/             # Level data
│   ├── level1.py       # Level 1 setup
│   └── loader.py       # Level loading logic
└── main.py             # Entry point
```

## Configuration (`environments.json`)

Environments are defined in JSON format:

```json
"Door": {
    "walkable": false,
    "texture_path": "",
    "color": [139, 69, 19],
    "width": 1,
    "height": 2,
    "trigger": "door"
}
```

## How to Run

1. Ensure Python and Pygame are installed.
2. Run the game from the root directory:
   ```bash
   python src/main.py
   ```
