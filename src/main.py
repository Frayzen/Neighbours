import random
import sys
import os
import argparse
import pygame
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
random.seed(39)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.game import Game

def start_game():
    try:
        print("Starting Normal Game...")
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try: pygame.quit()
        except: pass

def main():
    parser = argparse.ArgumentParser(description="Neighbours Game Launcher")
    parser.add_argument("--mode", type=str, default=None)
    args = parser.parse_args()
    mode = args.mode

    if mode is None:
        print("\n=== Neighbours Game Launcher ===")
        print("1. Play Normal Game")
        print("2. Fight Boss (Player vs AI)")
        print("3. Watch AI vs AI")
        print("4. Train Self Play (Standard)")
        print("5. Visualize AI Log")
        print("6. Train AMD Optimized (16 Cores)")
        print("7. Train AMD Extreme (28+ Threads)")
        print("================================")
        
        try:
            choice = input("Enter choice (1-7) [default: 1]: ").strip()
        except EOFError: choice = ""
            
        if choice == '2': mode = 'vs_boss_player'
        elif choice == '3': mode = 'vs_ai_watch'
        elif choice == '4': mode = 'train_self'
        elif choice == '5': mode = 'vis_log'
        elif choice == '6': mode = 'train_amd'
        elif choice == '7': mode = 'train_amd_smt'
        else: mode = 'play'
            
    print(f"Launching mode: {mode}")
    
    if mode == 'play':
        start_game()
    elif mode == 'vs_boss_player':
        try:
            from play_vs_ai import run; run(human_opponent=True)
        except Exception as e: print(e)
    elif mode == 'vs_ai_watch':
        try:
            from play_vs_ai import run; run(human_opponent=False)
        except Exception as e: print(e)
    elif mode == 'train_self':
        try:
            from train_self_play import train
            train(iterations=1000, n_envs=8, target="BOTH", use_history=True, cpu_profile="AUTO")
        except Exception as e: print(e)
    elif mode == 'train_amd':
        try:
            from train_self_play import train
            train(iterations=1000, n_envs=16, target="BOTH", use_history=True, cpu_profile="AMD_RYZEN_7950X")
        except Exception as e: print(e)
    elif mode == 'train_amd_smt':
        try:
            from train_self_play import train
            print("\n⚠️ WARNING: Extreme Mode loads logical cores. Ensure good cooling!")
            train(iterations=1000, n_envs=None, target="BOTH", use_history=True, cpu_profile="AMD_RYZEN_7950X_SMT")
        except Exception as e: print(e)
    elif mode == 'vis_log':
        try:
            from vis_log import run; run()
        except Exception as e: print(e)

if __name__ == "__main__":
    main()