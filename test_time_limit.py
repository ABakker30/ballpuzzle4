#!/usr/bin/env python3
"""
Simple test script to verify DLX engine time limit functionality.
This isolates the time limit logic from complex DLX operations.
"""

import time
import sys
import os

# Add the current directory to the path for module imports
sys.path.insert(0, os.path.dirname(__file__))

# Import DLX engine directly
from src.solver.engines.dlx_engine import DLXEngine

def test_time_limit_basic():
    """Test that DLX engine respects a very short time limit"""
    print("=== Testing DLX Engine Time Limit (5 seconds) ===")
    
    # Create a simple container - just use the 16-cell container
    container_data = {
        "coordinates": [
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
            [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1],
            [2, 0, 0], [0, 2, 0], [0, 0, 2], [2, 1, 0],
            [1, 2, 0], [2, 0, 1], [1, 0, 2], [0, 2, 1]
        ]
    }
    
    # Use a simple inventory - just a few pieces
    inventory = {"A": 1, "E": 1, "T": 1, "B": 1}
    
    # Create engine with 5-second time limit
    engine = DLXEngine()
    
    print(f"Starting DLX engine at {time.time():.2f}")
    start_time = time.time()
    
    # Run the engine with time limit
    solutions = []
    events = list(engine.solve(
        container=container_data,
        inventory=inventory,
        max_results=1000,
        seed=42,
        time_limit_seconds=5  # 5 second limit
    ))
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"Engine finished at {time.time():.2f}")
    print(f"Total elapsed time: {elapsed:.2f} seconds")
    
    # Check if it respected the time limit (allow 1 second tolerance)
    if elapsed <= 6.0:
        print("✅ SUCCESS: Engine respected the 5-second time limit")
        return True
    else:
        print(f"❌ FAILURE: Engine ran for {elapsed:.2f} seconds, exceeded 5-second limit")
        return False

def test_time_limit_immediate():
    """Test that DLX engine respects an immediate time limit"""
    print("\n=== Testing DLX Engine Immediate Time Limit (1 second) ===")
    
    container_data = {
        "coordinates": [
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
            [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1],
            [2, 0, 0], [0, 2, 0], [0, 0, 2], [2, 1, 0],
            [1, 2, 0], [2, 0, 1], [1, 0, 2], [0, 2, 1]
        ]
    }
    
    # Use all 25 pieces to make it harder
    inventory = {chr(ord('A') + i): 1 for i in range(25)}  # A-Y
    
    engine = DLXEngine()
    
    print(f"Starting DLX engine at {time.time():.2f}")
    start_time = time.time()
    
    # Run with very short time limit
    events = list(engine.solve(
        container=container_data,
        inventory=inventory,
        max_results=1000,
        seed=42,
        time_limit_seconds=1  # 1 second limit
    ))
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print(f"Engine finished at {time.time():.2f}")
    print(f"Total elapsed time: {elapsed:.2f} seconds")
    
    # Check if it respected the time limit (allow 0.5 second tolerance)
    if elapsed <= 1.5:
        print("✅ SUCCESS: Engine respected the 1-second time limit")
        return True
    else:
        print(f"❌ FAILURE: Engine ran for {elapsed:.2f} seconds, exceeded 1-second limit")
        return False

if __name__ == "__main__":
    print("Testing DLX Engine Time Limit Functionality")
    print("=" * 50)
    
    success1 = test_time_limit_basic()
    success2 = test_time_limit_immediate()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED: Time limit functionality works correctly")
    else:
        print("💥 TESTS FAILED: Time limit functionality needs debugging")
        
    print("Test completed.")
