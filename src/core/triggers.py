def trigger_door(game, x, y):
    print(f"Door triggered at {x}, {y}!")
    # Example: Toggle door state (requires more complex state management)
    # For now, just print.

def trigger_teleport(game, x, y):
    print("Teleporting player...")
    game.player.x = 100
    game.player.y = 100

TRIGGERS = {
    "door": trigger_door,
    "teleport": trigger_teleport
}

def execute_trigger(trigger_name, game, x, y):
    if trigger_name in TRIGGERS:
        TRIGGERS[trigger_name](game, x, y)
    else:
        print(f"Trigger '{trigger_name}' not found.")
