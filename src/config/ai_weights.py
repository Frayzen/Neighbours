# AI Training Weights and Parameters
# Adjust these variables to tune the AI's learning process.

# --- Reward Multipliers ---
# Multiplier for damage dealt to the opponent. Higher values encourage aggression.
REWARD_DMG_DEALT_MULTIPLIER = 5.0

# Multiplier for damage taken from the opponent. Higher values encourage defense.
REWARD_DMG_TAKEN_MULTIPLIER = 0.8



# --- Penalties ---
# Penalty applied every step to encourage faster wins (Existential Penalty).
REWARD_STEP_PENALTY = 0.05

# Penalty applied when the agent attacks but deals 0 damage (Whiffing).
REWARD_WHIFF_PENALTY = 0.2

# Penalty applied when the agent collides with a wall or is stuck (DuelEnv specific).
REWARD_WALL_COLLISION_PENALTY = 0.05

# Penalty applied when the game is declared a stalemate (no damage for N steps).
REWARD_STALEMATE_PENALTY = 0.3



# --- Bonuses ---
# Bonus applied per step for maintaining a specific distance range from the opponent.
REWARD_DISTANCE_BONUS = 0.1

# --- End Game Rewards ---
# Reward for winning the episode (killing the opponent).
REWARD_WIN = 100

# Penalty for losing the episode (dying).
# value is typically subtracted from the reward.
REWARD_LOSS = 50 

# --- Distance Constraints ---
# The logic will apply REWARD_DISTANCE_BONUS if distance is between MIN and MAX.
DISTANCE_BONUS_MIN = 200
DISTANCE_BONUS_MAX = 250
