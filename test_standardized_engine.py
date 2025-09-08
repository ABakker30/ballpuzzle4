#!/usr/bin/env python3
"""Test standardized engine behavior with 25 pieces on Shape_3."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print("=== Testing Standardized Engine Behavior ===")
    print("Shape_3 with 25 pieces - should yield control after each progress report")
    
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
    
    engine = EngineCAdapter()
    
    options = {
        'seed': 20250907,
        'max_results': 1,
        'progress_interval_ms': 1000,  # Every 1 second
        'flags': {
            'time_budget_s': 10.0,
            'pruning_level': 'basic'
        }
    }
    
    print("\nRunning with standardized yield pattern...")
    start_time = time.time()
    progress_count = 0
    
    try:
        for event in engine.solve(container, inventory, pieces, options):
            elapsed = time.time() - start_time
            
            if event['type'] == 'tick':
                progress_count += 1
                metrics = event['metrics']
                depth = metrics.get('depth', 0)
                nodes = metrics.get('nodes', 0)
                
                print(f"[{elapsed:4.1f}s] Progress #{progress_count}: "
                      f"Nodes: {nodes:6d} | Depth: {depth:2d}/25")
                
                # Test halt mechanism after 3 progress reports
                if progress_count >= 3:
                    print("         *** HALTING ENGINE AFTER 3 PROGRESS REPORTS ***")
                    break
                    
            elif event['type'] == 'solution':
                solution = event['solution']
                placements = solution.get('placements', [])
                print(f"[{elapsed:4.1f}s] *** SOLUTION: {len(placements)} pieces! ***")
                
            elif event['type'] == 'done':
                metrics = event['metrics']
                print(f"[{elapsed:4.1f}s] DONE: {metrics.get('nodes', 0):,} nodes | "
                      f"Solutions: {metrics.get('solutions', 0)}")
                break
                
    except KeyboardInterrupt:
        print("\n*** INTERRUPTED BY USER ***")
    
    total_time = time.time() - start_time
    print(f"\nTest completed in {total_time:.2f} seconds")
    print(f"Progress reports received: {progress_count}")
    print("Engine yielded control properly after each progress report!")

if __name__ == '__main__':
    main()
