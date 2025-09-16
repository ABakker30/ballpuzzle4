#!/usr/bin/env python3
"""Test Shape_3 with Engine-C for 10 seconds using 25 pieces."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print("=== Shape_3 Test: 10 seconds with 25 pieces ===")
    
    # Load Shape_3 container
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    
    # Create inventory with 25 pieces (theoretical perfect fit for 100 cells)
    inventory = {'pieces': {}}
    piece_count = 0
    
    # Use first 25 piece types
    for piece_id in 'ABCDEFGHIJKLMNOPQRSTUVWXY':
        if piece_id in pieces and piece_count < 25:
            inventory['pieces'][piece_id] = 1
            piece_count += 1
    
    print(f"Container: {len(container['coordinates'])} cells")
    print(f"Inventory: {sum(inventory['pieces'].values())} pieces")
    print(f"Piece types: {', '.join(sorted(inventory['pieces'].keys()))}")
    
    engine = EngineCAdapter()
    
    # 10-second test with 1-second updates
    options = {
        'seed': 20250907,
        'max_results': 1,
        'progress_interval_ms': 1000,  # Every 1 second
        'flags': {
            'time_budget_s': 10.0,  # Exactly 10 seconds
            'pruning_level': 'basic'
        }
    }
    
    print("\nRunning for 10 seconds with 25 pieces...")
    start_time = time.time()
    
    for event in engine.solve(container, inventory, pieces, options):
        elapsed = time.time() - start_time
        
        if event['type'] == 'tick':
            metrics = event['metrics']
            depth = metrics.get('depth', 0)
            progress_pct = (depth / 25) * 100 if depth > 0 else 0
            
            print(f"[{elapsed:4.1f}s] Nodes: {metrics.get('nodes', 0):6d} | "
                  f"Depth: {depth:2d}/25 ({progress_pct:4.1f}%) | "
                  f"Pruned: {metrics.get('pruned', 0):6d}")
            
        elif event['type'] == 'solution':
            solution = event['solution']
            placements = solution.get('placements', [])
            cells_covered = len(placements) * 4
            coverage_pct = (cells_covered / 100) * 100
            
            print(f"[{elapsed:4.1f}s] *** SOLUTION FOUND! ***")
            print(f"         Pieces: {len(placements)}/25 | "
                  f"Cells: {cells_covered}/100 ({coverage_pct:.1f}%)")
            
            if len(placements) == 25:
                print("         *** PERFECT SOLUTION - ALL 25 PIECES! ***")
            
        elif event['type'] == 'done':
            metrics = event['metrics']
            final_depth = metrics.get('bestDepth', 0)
            final_coverage = (final_depth * 4 / 100) * 100
            
            print(f"[{elapsed:4.1f}s] DONE: {metrics.get('nodes', 0):,} nodes | "
                  f"Max depth: {final_depth}/25 ({final_coverage:.1f}%) | "
                  f"Solutions: {metrics.get('solutions', 0)}")
            
            if metrics.get('solutions', 0) > 0:
                print("         *** COMPLETE SOLUTION ACHIEVED! ***")
            else:
                remaining_pieces = 25 - final_depth
                remaining_cells = 100 - (final_depth * 4)
                print(f"         Partial: {remaining_pieces} pieces, {remaining_cells} cells remaining")
            
            break
    
    total_time = time.time() - start_time
    print(f"\nCompleted in {total_time:.2f} seconds")

if __name__ == '__main__':
    main()
