#!/usr/bin/env python3
"""Simple cycle-based test for Engine-C with immediate feedback."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print("=== Simple Engine-C Cycle Test ===")
    
    # Load container and pieces
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    
    # Small inventory for quick test
    inventory = {'pieces': {'A': 1, 'B': 1, 'C': 1}}
    
    print(f"Container: {len(container['coordinates'])} cells")
    print(f"Inventory: {sum(inventory['pieces'].values())} pieces")
    
    engine = EngineCAdapter()
    
    # Very short time budget to test stopping
    options = {
        'seed': 20250907,
        'max_results': 1,
        'progress_interval_ms': 500,  # Progress every 0.5 seconds
        'flags': {
            'time_budget_s': 5.0,  # Only 5 seconds
            'pruning_level': 'basic'
        }
    }
    
    print("\nRunning Engine-C for 5 seconds max...")
    start_time = time.time()
    
    event_count = 0
    for event in engine.solve(container, inventory, pieces, options):
        event_count += 1
        elapsed = time.time() - start_time
        
        print(f"[{elapsed:.1f}s] Event #{event_count}: {event['type']}")
        
        if event['type'] == 'tick':
            metrics = event.get('metrics', {})
            print(f"  Nodes: {metrics.get('nodes', 0)}, Depth: {metrics.get('depth', 0)}")
            
        elif event['type'] == 'solution':
            solution = event['solution']
            placements = solution.get('placements', [])
            print(f"  Solution with {len(placements)} pieces!")
            
        elif event['type'] == 'done':
            metrics = event['metrics']
            print(f"  Final: {metrics.get('nodes', 0)} nodes, {metrics.get('solutions', 0)} solutions")
            break
    
    total_time = time.time() - start_time
    print(f"\nCompleted in {total_time:.2f}s with {event_count} events")

if __name__ == '__main__':
    main()
