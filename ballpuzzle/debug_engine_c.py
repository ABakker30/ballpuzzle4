#!/usr/bin/env python3
"""Debug Engine-C candidate generation and search behavior."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print("=== Debugging Engine-C Behavior ===")
    
    # Load Shape_3 container
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    
    print(f"Container: {len(container['coordinates'])} cells")
    print(f"Available pieces: {len(pieces)} ({', '.join(sorted(pieces.keys()))})")
    
    # Test with just 4 pieces first
    inventory = {'pieces': {'A': 1, 'B': 1, 'C': 1, 'D': 1}}
    
    print(f"Testing with 4 pieces: {list(inventory['pieces'].keys())}")
    
    engine = EngineCAdapter()
    
    options = {
        'seed': 20250907,
        'max_results': 1,
        'progress_interval_ms': 500,  # Every 0.5 seconds
        'flags': {
            'time_budget_s': 5.0,
            'pruning_level': 'basic'
        }
    }
    
    print("\nRunning 4-piece test...")
    start_time = time.time()
    
    for event in engine.solve(container, inventory, pieces, options):
        elapsed = time.time() - start_time
        
        if event['type'] == 'tick':
            metrics = event['metrics']
            print(f"[{elapsed:4.1f}s] Progress: Nodes: {metrics.get('nodes', 0):6d} | "
                  f"Depth: {metrics.get('depth', 0):2d}/4")
                  
        elif event['type'] == 'solution':
            solution = event['solution']
            placements = solution.get('placements', [])
            print(f"[{elapsed:4.1f}s] *** SOLUTION: {len(placements)} pieces! ***")
            
        elif event['type'] == 'done':
            metrics = event['metrics']
            print(f"[{elapsed:4.1f}s] DONE: {metrics.get('nodes', 0):,} nodes | "
                  f"Solutions: {metrics.get('solutions', 0)}")
            break
    
    total_time = time.time() - start_time
    print(f"\n4-piece test completed in {total_time:.2f} seconds")
    
    # Now test with more pieces
    print("\n" + "="*50)
    inventory = {'pieces': {}}
    for i, piece_id in enumerate('ABCDEFGHIJ'):  # 10 pieces
        if piece_id in pieces:
            inventory['pieces'][piece_id] = 1
            
    print(f"Testing with 10 pieces: {list(inventory['pieces'].keys())}")
    
    start_time = time.time()
    
    for event in engine.solve(container, inventory, pieces, options):
        elapsed = time.time() - start_time
        
        if event['type'] == 'tick':
            metrics = event['metrics']
            print(f"[{elapsed:4.1f}s] Progress: Nodes: {metrics.get('nodes', 0):6d} | "
                  f"Depth: {metrics.get('depth', 0):2d}/10")
                  
        elif event['type'] == 'solution':
            solution = event['solution']
            placements = solution.get('placements', [])
            print(f"[{elapsed:4.1f}s] *** SOLUTION: {len(placements)} pieces! ***")
            
        elif event['type'] == 'done':
            metrics = event['metrics']
            print(f"[{elapsed:4.1f}s] DONE: {metrics.get('nodes', 0):,} nodes | "
                  f"Solutions: {metrics.get('solutions', 0)}")
            break
    
    total_time = time.time() - start_time
    print(f"\n10-piece test completed in {total_time:.2f} seconds")

if __name__ == '__main__':
    main()
