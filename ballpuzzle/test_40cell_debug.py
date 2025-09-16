#!/usr/bin/env python3
"""
Test DFS engine with detailed debugging to find the exact failure point.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.solver.registry import get_engine
from src.io.container import load_container

def main():
    print("=== 40-Cell Container DFS Debug Test ===")
    
    # Load container
    container = load_container("data/containers/v1/40 cell.fcc.json")
    print(f"Container: {len(container['cells'])} cells")
    
    # Setup engine with minimal piece inventory for faster testing
    engine = get_engine("dfs")
    inventory = {}
    
    # Use just A and B pieces to simplify debugging
    pieces = {"A": 10, "B": 10}  # Should be enough for 10 pieces needed
    
    options = {
        "time_limit": 10,  # Shorter time limit
        "max_results": 1,
        "seed": 42
    }
    
    print(f"Piece inventory: {pieces}")
    print("Starting DFS engine with debug output...")
    
    t0 = time.time()
    events_received = 0
    
    try:
        for event in engine.solve(container, inventory, pieces, options):
            events_received += 1
            elapsed = time.time() - t0
            
            print(f"[{elapsed:6.2f}s] Event #{events_received}: {event['type']}")
            
            if event["type"] == "solution":
                print(f"  Solution found!")
                
            elif event["type"] == "tick":
                print(f"  Progress tick: {event.get('msg', 'no message')}")
                
            elif event["type"] == "done":
                print(f"  Search completed")
                if "metrics" in event:
                    metrics = event["metrics"]
                    print(f"  Metrics: {metrics}")
                break
                
    except Exception as e:
        print(f"Exception during solve: {e}")
        import traceback
        traceback.print_exc()
    
    elapsed_total = time.time() - t0
    print(f"\nTest completed after {elapsed_total:.2f}s")
    print(f"Total events received: {events_received}")

if __name__ == "__main__":
    main()
