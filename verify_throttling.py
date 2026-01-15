
import sys
import os
sys.path.append(os.path.abspath("src"))
from ai.duel_env import DuelEnv
from unittest.mock import MagicMock

def test_throttling():
    print("--- Testing Throttling Logic ---")
    
    # Test 1: Training Mode (Headless, Should skip 4 frames, AI runs every 1 step)
    print("\n[Test 1] Training Mode (Headless=True)")
    env_train = DuelEnv(mode="TRAIN_BOSS", headless=True, human_opponent=False)
    print(f"Frame Skip: {env_train.frame_skip}")
    print(f"AI Run Period: {env_train.ai_run_period}")
    
    if env_train.frame_skip != 4:
        print("FAIL: Frame skip should be 4 in training mode")
    if env_train.ai_run_period != 1:
        print("FAIL: AI Run Period should be 1 in training mode")

    # Mock the prediction to count calls
    env_train.opponent_model = MagicMock()
    env_train.opponent_model.predict.return_value = (0, None)
    
    for _ in range(4):
        env_train.step(0)
        
    print(f"Steps: 4, AI Calls: {env_train.opponent_model.predict.call_count}")
    if env_train.opponent_model.predict.call_count == 4:
        print("PASS: AI called every step (15Hz equivalent)")
    else:
        print(f"FAIL: Expected 4 calls, got {env_train.opponent_model.predict.call_count}")

    # Test 2: Watch Mode (Headless=False, Should skip 1 frame, AI runs every 4 steps)
    try:
        # We need to mock pygame display to avoid window opening
        import pygame
        pygame.display.set_mode = MagicMock()
        
        print("\n[Test 2] Watch Mode (Headless=False)")
        env_watch = DuelEnv(mode="TRAIN_BOSS", headless=False, human_opponent=False)
        print(f"Frame Skip: {env_watch.frame_skip}")
        print(f"AI Run Period: {env_watch.ai_run_period}")
        
        if env_watch.frame_skip != 1:
            print("FAIL: Frame skip should be 1 in watch mode")
        if env_watch.ai_run_period != 4:
            print("FAIL: AI Run Period should be 4 in watch mode")
            
        env_watch.opponent_model = MagicMock()
        env_watch.opponent_model.predict.return_value = (0, None)
        
        # Step 20 times (should be 5 AI calls)
        for _ in range(20):
            env_watch.step(0)
            
        print(f"Steps: 20, AI Calls: {env_watch.opponent_model.predict.call_count}")
        if env_watch.opponent_model.predict.call_count == 5:
            print("PASS: AI called every 4 steps (15Hz equivalent)")
        else:
            print(f"FAIL: Expected 5 calls, got {env_watch.opponent_model.predict.call_count}")

    except Exception as e:
        print(f"Test 2 Failed with exception: {e}")

if __name__ == "__main__":
    test_throttling()
