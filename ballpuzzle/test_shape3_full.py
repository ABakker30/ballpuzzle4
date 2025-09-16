#!/usr/bin/env python3
"""Test Shape_3 with Engine-C using full piece inventory to find complete solution."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import json
import time

def main():
    print('=== Testing Shape_3 with Engine-C Full Inventory ===')
    
    # Load Shape_3 container
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    total_cells = len(container['coordinates'])
    print(f'Shape_3 container: {total_cells} cells')
    
    # Calculate pieces needed (each piece is 4 cells)
    pieces_needed = total_cells // 4
    remainder = total_cells % 4
    print(f'Theoretical pieces needed: {pieces_needed} (4-cell pieces)')
    if remainder:
        print(f'Remainder: {remainder} cells (container not perfectly divisible by 4)')
    
    # Load all pieces A-Y
    pieces = load_fcc_A_to_Y()
    print(f'Available piece types: {len(pieces)} (A-Y)')
    
    # Test with generous inventory - enough pieces to potentially fill container
    inventory = {'pieces': {}}
    for piece_id in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        if piece_id in pieces:
            inventory['pieces'][piece_id] = 5  # 5 of each piece type
    
    print(f'Testing with inventory: {sum(inventory["pieces"].values())} total pieces')
    print('Piece counts:', ', '.join([f'{k}={v}' for k, v in inventory['pieces'].items()]))
    
    engine = EngineCAdapter()
    options = {
        'seed': 20250907,
        'flags': {
            'max_results': 1,
            'time_budget_s': 120.0,  # 2 minute budget
            'pruning_level': 'basic',
            'shuffle': 'ties_only'
        }
    }
    
    print('\nStarting solve...')
    start_time = time.time()
    
    events = []
    solution_found = False
    max_depth = 0
    
    for event in engine.solve(container, inventory, pieces, options):
        events.append(event)
        
        if event['type'] == 'solution':
            solution_found = True
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
            
            if solution_found:
                print('*** COMPLETE SOLUTION ACHIEVED! ***')
            else:
                print('No complete solution found with current inventory')
                print(f'Max depth {metrics["bestDepth"]} suggests {metrics["bestDepth"]} pieces were placed')
    
    print('\n=== Shape_3 Full Test Complete ===')

if __name__ == '__main__':
    main()
