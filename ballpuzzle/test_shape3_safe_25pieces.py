#!/usr/bin/env python3
"""Test Shape_3 with Engine-C for 10 seconds using 25 pieces with safety limits."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print("=== Shape_3 Test: 10 seconds with 25 pieces (SAFE MODE) ===")
    
    # Load Shape_3 container
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    
    # Create inventory with 25 pieces
    inventory = {'pieces': {}}
    piece_count = 0
    
    for piece_id in 'ABCDEFGHIJKLMNOPQRSTUVWXY':
        if piece_id in pieces and piece_count < 25:
            inventory['pieces'][piece_id] = 1
            piece_count += 1
    
    print(f"Container: {len(container['coordinates'])} cells")
    print(f"Inventory: {sum(inventory['pieces'].values())} pieces")
    print("Safety limits: 50,000 nodes max, 10 second timeout")
    
    engine = EngineCAdapter()
    
    options = {
        'seed': 20250907,
        'max_results': 1,
        'progress_interval_ms': 2000,  # Every 2 seconds 
        'flags': {
            'time_budget_s': 10.0,
            'pruning_level': 'basic'
        }
    }
    
    print("\nRunning with safety limits...")
    start_time = time.time()
    
    for event in engine.solve(container, inventory, pieces, options):
        elapsed = time.time() - start_time
        
        if event['type'] == 'tick':
            metrics = event['metrics']
            depth = metrics.get('depth', 0)
            nodes = metrics.get('nodes', 0)
            
            print(f"[{elapsed:4.1f}s] Nodes: {nodes:6d}/50000 | "
                  f"Depth: {depth:2d}/25 | "
                  f"Rate: {nodes/elapsed:.0f}/s")
            
        elif event['type'] == 'solution':
            solution = event['solution']
            placements = solution.get('placements', [])
            print(f"[{elapsed:4.1f}s] *** SOLUTION: {len(placements)} pieces! ***")
            
        elif event['type'] == 'done':
            metrics = event['metrics']
            nodes = metrics.get('nodes', 0)
            depth = metrics.get('bestDepth', 0)
            
            print(f"[{elapsed:4.1f}s] DONE: {nodes:,} nodes | "
                  f"Depth: {depth}/25 | "
                  f"Solutions: {metrics.get('solutions', 0)}")
            
            if nodes >= 50000:
                print("         *** STOPPED AT NODE LIMIT (50,000) ***")
            elif elapsed >= 10.0:
                print("         *** STOPPED AT TIME LIMIT (10s) ***")
            
            break
    
    total_time = time.time() - start_time
    print(f"\nCompleted safely in {total_time:.2f} seconds")

if __name__ == '__main__':
    main()
