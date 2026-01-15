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
        print("5. Visualize AI Log")
        print("================================")
        
        try:
            choice = input("Enter choice (1-5) [default: 1]: ").strip()
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
            
            # CPU Profile Selection
            print("\n--- CPU Optimization Profile ---")
            print("[1] Auto-Detect (Recommended)")
            print("[2] AMD Ryzen 7950X (16C/32T → 24 workers)")
            print("[3] Intel i7 11th Gen (8C/16T → 12 workers)")
            print("[4] Custom (Manual worker count)")
            
            cpu_profile = 'AUTO'
            n_envs = None
            
            try:
                cpu_choice = input("Select CPU profile (1-4) [default: 1]: ").strip()
                
                if cpu_choice == '2':
                    cpu_profile = 'AMD_RYZEN_7950X'
                    print("✓ Using AMD Ryzen 7950X profile (24 workers)")
                elif cpu_choice == '3':
                    cpu_profile = 'INTEL_I7_11GEN'
                    print("✓ Using Intel i7 11th Gen profile (12 workers)")
                elif cpu_choice == '4':
                    # Custom worker count
                    cpu_profile = 'AUTO'
                    try:
                        envs_input = input("Enter number of parallel workers [default: auto]: ").strip()
                        n_envs = int(envs_input) if envs_input else None
                        if n_envs:
                            print(f"✓ Using custom worker count: {n_envs}")
                    except ValueError:
                        print("Invalid input. Using auto-detect.")
                        n_envs = None
                else:
                    # Auto-detect (default)
                    cpu_profile = 'AUTO'
                    print("✓ Using auto-detect (will detect your CPU)")
                    
            except Exception:
                cpu_profile = 'AUTO'
                print("Using auto-detect")
                
            # Prompt for History Usage
            use_hist = False
            try:
                h_input = input("\nUse League History (Old Versions)? [y/N]: ").strip().lower()
                if h_input == 'y':
                    use_hist = True
            except:
                pass
                
            # Prompt for Training Target
            print("\nSelect Training Target:")
            print("[1] Both (Ping-Pong)")
            print("[2] Boss Only")
            print("[3] Alice Only")
            
            target_map = {"1": "BOTH", "2": "BOSS", "3": "PLAYER"}
            try:
                t_input = input("Enter choice (1-3) [default: 1]: ").strip()
                target_choice = target_map.get(t_input, "BOTH")
            except Exception:
                target_choice = "BOTH"
            
            # Call Train with CPU profile
            train(
                iterations=iterations, 
                n_envs=n_envs, 
                target=target_choice, 
                use_history=use_hist,
                cpu_profile=cpu_profile
            )
            
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