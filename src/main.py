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
        try:
            pygame.quit()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description="Neighbours Game Launcher")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=['play', 'train_boss', 'vs_ai', 'train_self', 'train_amd'], 
        default=None,
        help="Select the game mode."
    )
    
    args = parser.parse_args()
    mode = args.mode

    if mode is None:
        print("\n=== Neighbours Game Launcher ===")
        print("1. Play Normal Game")
        print("2. Fight Boss (Player vs AI)")
        print("3. Watch AI vs AI")
        print("4. Train Self Play (Standard)")
        print("5. Visualize AI Log")
        print("6. Train AMD Optimized (Ryzen 7950X)")
        print("================================")
        
        try:
            choice = input("Enter choice (1-6) [default: 1]: ").strip()
        except EOFError:
            choice = ""
            
        if choice == '2':
            mode = 'vs_boss_player'
        elif choice == '3':
            mode = 'vs_ai_watch'
        elif choice == '4':
            mode = 'train_self'
        elif choice == '5':
            mode = 'vis_log'
        elif choice == '6':
            mode = 'train_amd'
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
            
            print("\n--- Standard Self-Play Configuration ---")
            try:
                iters_input = input("Enter number of iterations [default: Infinite]: ").strip()
                iterations = int(iters_input) if iters_input else float('inf')
            except ValueError:
                iterations = float('inf')
                
            try:
                envs_input = input(f"Enter number of parallel games [default: 8]: ").strip()
                n_envs = int(envs_input) if envs_input else 8
            except ValueError:
                n_envs = 8
            
            train(iterations=iterations, n_envs=n_envs, target="BOTH", use_history=True, cpu_profile="AUTO")
            
        except ImportError as e:
             print(f"Error importing train_self_play: {e}")
        except Exception as e:
             print(f"Error running train_self_play: {e}")

    elif mode == 'train_amd':
        try:
            from train_self_play import train
            print("\n--- AMD Ryzen 7950X Unleashed Mode ---")
            print("Settings: 16 Workers, High-Bandwidth Training, CCD-Pinning enabled.")
            
            try:
                iters_input = input("Enter number of iterations [default: Infinite]: ").strip()
                iterations = int(iters_input) if iters_input else float('inf')
            except ValueError:
                iterations = float('inf')
            
            # Force Ryzen Profile
            train(iterations=iterations, n_envs=16, target="BOTH", use_history=True, cpu_profile="AMD_RYZEN_7950X")
            
        except ImportError as e:
             print(f"Error importing train_self_play: {e}")
        except Exception as e:
             print(f"Error running train_self_play: {e}")

    elif mode == 'vis_log':
        try:
            from vis_log import run as vis_run
            vis_run()
        except ImportError as e:
             print(f"Error importing vis_log: {e}")
        except Exception as e:
             print(f"Error running vis_log: {e}")


if __name__ == "__main__":
    main()