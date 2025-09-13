#!/usr/bin/env python3
"""
Test DFS engine on 40-cell container with verbose debugging.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.solver.registry import get_engine
from src.io.container import load_container

def main():
    print("=== 40-Cell Container DFS Test (30 seconds) ===")
    
    # Load container
    container = load_container("data/containers/v1/40 cell.fcc.json")
    print(f"Container: {len(container['cells'])} cells")
    print(f"Pieces needed: {len(container['cells']) // 4}")
    
    # Setup engine with reduced piece inventory to speed up combination generation
    engine = get_engine("dfs")
    inventory = {}
    
    # Use smaller piece inventory to reduce combination explosion
    pieces = {"A": 10, "B": 10, "C": 10, "D": 10, "E": 10}  # Still plenty for 10 pieces needed
    
    options = {
        "time_limit": 30,
        "max_results": 3,
        "seed": 42,
        "progress_interval_ms": 1000,
        "status_json": None,
        "status_interval_ms": 1000
    }
    
    print(f"Piece inventory: {pieces}")
    print(f"Total pieces available: {sum(pieces.values())}")
    print("Starting DFS engine...")
    
    t0 = time.time()
    solution_count = 0
    last_progress = 0
    
    try:
        for event in engine.solve(container, inventory, pieces, options):
            elapsed = time.time() - t0
            
            if event["type"] == "solution":
                solution_count += 1
                print(f"[{elapsed:6.1f}s] Solution {solution_count} found!")
                
            elif event["type"] == "tick":
                print(f"[{elapsed:6.1f}s] Progress tick")
                
            elif event["type"] == "done":
                print(f"[{elapsed:6.1f}s] Search completed")
                if "metrics" in event:
                    metrics = event["metrics"]
                    print("Final Results:")
                    print(f"  Solutions found: {metrics.get('solutions_found', 0)}")
                    print(f"  Nodes explored: {metrics.get('nodes_explored', 0)}")
                    print(f"  Max depth: {metrics.get('max_depth_reached', 0)}")
                    print(f"  Max pieces placed: {metrics.get('max_pieces_placed', 0)}")
                    print(f"  Search time: {metrics.get('time_elapsed', 0):.2f}s")
                break
            
            # Show progress every 5 seconds
            if elapsed - last_progress >= 5:
                print(f"[{elapsed:6.1f}s] Still searching...")
                last_progress = elapsed
                
    except Exception as e:
        print(f"Error during solve: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nTest completed after {time.time() - t0:.1f}s")
    print(f"Total solutions found: {solution_count}")

if __name__ == "__main__":
    main()
