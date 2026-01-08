from core.debug import debug

def trigger_door(game, x, y):
    debug.log(f"Door triggered at {x}, {y}!")
    # Example: Toggle door state (requires more complex state management)
    # For now, just print.

def trigger_teleport(game, x, y):
    debug.log("Teleporting player...")
    game.player.x = 100
    game.player.y = 100

def trigger_trapdoor(game, x, y):
    debug.log("Player stepped on trapdoor! Going to next layer...")
    game.next_layer()

TRIGGERS = {
    "door": trigger_door,
    "teleport": trigger_teleport,
    "trapdoor": trigger_trapdoor
}

def execute_trigger(trigger_name, game, x, y):
    if trigger_name in TRIGGERS:
        TRIGGERS[trigger_name](game, x, y)
    else:
        debug.log(f"Trigger '{trigger_name}' not found.")
