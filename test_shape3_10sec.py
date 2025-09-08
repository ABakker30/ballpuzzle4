#!/usr/bin/env python3
"""Test Shape_3 with Engine-C for exactly 10 seconds with 1-second progress updates."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print("=== Shape_3 Test: 10 seconds, 1-second updates ===")
    
    # Load Shape_3 container
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    
    # Small inventory to avoid excessive search space
    inventory = {'pieces': {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1}}
    
    print(f"Container: {len(container['coordinates'])} cells")
    print(f"Inventory: {sum(inventory['pieces'].values())} pieces")
    
    engine = EngineCAdapter()
    
    # Strict 10-second test with 1-second updates
    options = {
        'seed': 20250907,
        'max_results': 1,
        'progress_interval_ms': 1000,  # Every 1 second
        'flags': {
            'time_budget_s': 10.0,  # Exactly 10 seconds
            'pruning_level': 'basic'
        }
    }
    
    print("\nRunning for exactly 10 seconds with 1-second updates...")
    start_time = time.time()
    
    for event in engine.solve(container, inventory, pieces, options):
        elapsed = time.time() - start_time
        
        if event['type'] == 'tick':
            metrics = event['metrics']
            print(f"[{elapsed:4.1f}s] Nodes: {metrics.get('nodes', 0):5d} | "
                  f"Depth: {metrics.get('depth', 0):2d} | "
                  f"Pruned: {metrics.get('pruned', 0):5d}")
            
        elif event['type'] == 'solution':
            solution = event['solution']
            placements = solution.get('placements', [])
            print(f"[{elapsed:4.1f}s] *** SOLUTION: {len(placements)} pieces placed! ***")
            
        elif event['type'] == 'done':
            metrics = event['metrics']
            print(f"[{elapsed:4.1f}s] DONE: {metrics.get('nodes', 0)} nodes, "
                  f"depth {metrics.get('bestDepth', 0)}, "
                  f"{metrics.get('solutions', 0)} solutions")
            break
    
    total_time = time.time() - start_time
    print(f"\nCompleted in {total_time:.2f} seconds")

if __name__ == '__main__':
    main()
