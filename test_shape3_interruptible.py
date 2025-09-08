#!/usr/bin/env python3
"""Test Shape_3 with Engine-C using interruptible search with progress updates."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print('=== Testing Shape_3 with Engine-C (Interruptible) ===')
    
    # Load Shape_3 container
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    total_cells = len(container['coordinates'])
    print(f'Shape_3 container: {total_cells} cells')
    
    # Load pieces and create reasonable inventory
    pieces = load_fcc_A_to_Y()
    inventory = {'pieces': {}}
    
    # Use fewer pieces to avoid excessive search space
    for piece_id in 'ABCDEFGHIJ':  # Just first 10 pieces
        if piece_id in pieces:
            inventory['pieces'][piece_id] = 2  # 2 of each
    
    print(f'Testing with inventory: {sum(inventory["pieces"].values())} total pieces')
    print('Piece counts:', ', '.join([f'{k}={v}' for k, v in inventory['pieces'].items()]))
    
    engine = EngineCAdapter()
    options = {
        'seed': 20250907,
        'flags': {
            'max_results': 1,
            'time_budget_s': 30.0,  # 30 second budget
            'pruning_level': 'basic',
            'shuffle': 'ties_only'
        },
        'progress_interval_ms': 2000  # Progress every 2 seconds
    }
    
    print('\nStarting interruptible solve...')
    start_time = time.time()
    
    max_depth_reached = 0
    nodes_explored = 0
    progress_updates = 0
    
    try:
        for event in engine.solve(container, inventory, pieces, options):
            if event['type'] == 'tick':
                progress_updates += 1
                metrics = event['metrics']
                elapsed = time.time() - start_time
                
                print(f'Progress #{progress_updates}: {metrics["nodes"]} nodes, depth {metrics["depth"]}, {elapsed:.1f}s')
                max_depth_reached = max(max_depth_reached, metrics["depth"])
                nodes_explored = metrics["nodes"]
                
                # Allow user to see progress and interrupt if needed
                
            elif event['type'] == 'solution':
                solution = event['solution']
                placements = solution['placements']
                
                print(f'\n*** SOLUTION FOUND! ***')
                print(f'Pieces placed: {len(placements)}')
                print(f'Cells covered: {len(placements) * 4}')
                
                # Show which pieces were used
                pieces_used = {}
                for placement in placements:
                    piece_id = placement['piece']
                    pieces_used[piece_id] = pieces_used.get(piece_id, 0) + 1
                
                print('Pieces used:', ', '.join([f'{k}={v}' for k, v in sorted(pieces_used.items())]))
                
            elif event['type'] == 'done':
                elapsed = time.time() - start_time
                metrics = event['metrics']
                
                print(f'\nSearch completed in {elapsed:.2f}s')
                print(f'Solutions found: {metrics["solutions"]}')
                print(f'Nodes explored: {metrics["nodes"]}')
                print(f'Nodes pruned: {metrics["pruned"]}')
                print(f'Max depth reached: {metrics["bestDepth"]}')
                print(f'Progress updates: {progress_updates}')
                
                if metrics["solutions"] > 0:
                    print('*** COMPLETE SOLUTION ACHIEVED! ***')
                else:
                    print(f'No complete solution found. Max depth {metrics["bestDepth"]} suggests {metrics["bestDepth"]} pieces were placed')
    
    except KeyboardInterrupt:
        print('\n*** Search interrupted by user ***')
        print(f'Max depth reached: {max_depth_reached} pieces')
        print(f'Nodes explored: {nodes_explored}')
    
    print('\n=== Shape_3 Interruptible Test Complete ===')

if __name__ == '__main__':
    main()
