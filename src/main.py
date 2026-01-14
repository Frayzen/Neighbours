import random
import sys
import os
import argparse
import pygame
import warnings

# Suppress pkg_resources deprecation warning from pygame/setuptools
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# Set random seed
random.seed(39)

# Fix Path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports
from core.game import Game

def start_game():
    """
    Initializes and runs the standard game loop.
    """
    try:
        print("Starting Normal Game...")
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure we can return cleanly if game crashes or closes
        try:
            pygame.quit()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description="Neighbours Game Launcher")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=['play', 'train_boss', 'vs_ai', 'train_self'], 
        default=None,
        help="Select the game mode: 'play', 'train_boss', 'vs_ai', or 'train_self'."
    )
    
    args = parser.parse_args()
    mode = args.mode

    if mode is None:
        print("\n=== Neighbours Game Launcher ===")
        print("1. Play Normal Game")
        print("2. Fight Boss (Player vs AI)")
        print("3. Watch AI vs AI")
        print("4. Train Self Play (Ping-Pong)")
        print("================================")
        
        try:
            choice = input("Enter choice (1-4) [default: 1]: ").strip()
        except EOFError:
            choice = ""
            
        if choice == '2':
            mode = 'vs_boss_player'
        elif choice == '3':
            mode = 'vs_ai_watch'
        elif choice == '4':
            mode = 'train_self'
        else:
            mode = 'play'
            
    print(f"Launching mode: {mode}")
    
    if mode == 'play':
        start_game()
        
    elif mode == 'vs_boss_player':
        try:
            from play_vs_ai import run as vs_ai_run
            vs_ai_run(human_opponent=True)
        except ImportError as e:
            print(f"Error importing play_vs_ai: {e}")
        except Exception as e:
             print(f"Error running vs_boss_player: {e}")

    elif mode == 'vs_ai_watch':
        try:
            from play_vs_ai import run as vs_ai_run
            vs_ai_run(human_opponent=False)
        except ImportError as e:
             print(f"Error importing play_vs_ai: {e}")
        except Exception as e:
             print(f"Error running vs_ai_watch: {e}")

    elif mode == 'train_self':
        try:
            from train_self_play import train
            
            # Default values
            default_iters = float('inf')
            default_envs = 8
            
            # Prompt for Iterations
            try:
                iters_input = input("Enter number of iterations [default: Infinite]: ").strip()
                if not iters_input:
                    iterations = float('inf')
                else:
                    iterations = int(iters_input)
            except ValueError:
                print("Invalid input. Using default: Infinite")
                iterations = float('inf')
                
            # Prompt for Parallel Envs
            try:
                envs_input = input(f"Enter number of parallel games [default: {default_envs}]: ").strip()
                n_envs = int(envs_input) if envs_input else default_envs
            except ValueError:
                print(f"Invalid input. Using default: {default_envs}")
                n_envs = default_envs
                
            # Prompt for Training Target
            print("Select Training Target:")
            print("[1] Both (Ping-Pong)")
            print("[2] Boss Only")
            print("[3] Alice Only")
            
            target_map = {"1": "BOTH", "2": "BOSS", "3": "PLAYER"}
            try:
                t_input = input("Enter choice (1-3) [default: 1]: ").strip()
                target_choice = target_map.get(t_input, "BOTH")
            except Exception:
                target_choice = "BOTH"
            
            train(iterations=iterations, n_envs=n_envs, target=target_choice)
        except ImportError as e:
             print(f"Error importing train_self_play: {e}")
        except Exception as e:
             print(f"Error running train_self_play: {e}")

if __name__ == "__main__":
    main()
