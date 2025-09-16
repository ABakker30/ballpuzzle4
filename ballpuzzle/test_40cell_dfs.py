#!/usr/bin/env python3
"""
Test DFS engine on 40-cell container for 30 seconds with progress logging.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.solver.registry import get_engine
from src.io.container import load_container

def main():
    print("Loading 40-cell container...")
    container = load_container("data/containers/v1/40 cell.fcc.json")
    print(f"Container loaded: {len(container['cells'])} cells")
    
    print("Starting DFS engine for 30 seconds...")
    engine = get_engine("dfs")
    inventory = {}
    pieces = {"A": 25, "B": 25, "C": 25, "D": 25, "E": 25}
    options = {
        "time_limit": 30,
        "max_results": 10,
        "seed": 42,
        "progress_interval_ms": 2000
    }
    
    t0 = time.time()
    solution_count = 0
    
    print("Engine starting...")
    for event in engine.solve(container, inventory, pieces, options):
        elapsed = time.time() - t0
        
        if event["type"] == "solution":
            solution_count += 1
            print(f"Solution {solution_count} found at {elapsed:.1f}s")
            
        elif event["type"] == "tick":
            print(f"Progress tick at {elapsed:.1f}s")
            
        elif event["type"] == "done":
            print(f"Search completed in {elapsed:.1f}s")
            if "metrics" in event:
                metrics = event["metrics"]
                print("Final metrics:")
                print(f"  Solutions found: {metrics.get('solutions_found', 0)}")
                print(f"  Nodes explored: {metrics.get('nodes_explored', 0)}")
                print(f"  Max depth reached: {metrics.get('max_depth_reached', 0)}")
                print(f"  Max pieces placed: {metrics.get('max_pieces_placed', 0)}")
                print(f"  Time elapsed: {metrics.get('time_elapsed', 0):.2f}s")
            break
    
    print(f"Test completed. Total solutions: {solution_count}")

if __name__ == "__main__":
    main()
