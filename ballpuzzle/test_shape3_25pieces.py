#!/usr/bin/env python3
"""Test Shape_3 with 25 pieces for short duration to see placement progress."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print("=== Shape_3 Test with 25 Pieces ===")
    
    # Load Shape_3 container (100 cells)
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    
    total_cells = len(container['coordinates'])
    theoretical_pieces_needed = total_cells // 4  # 25 pieces for 100 cells
    
    print(f"Container: {total_cells} cells")
    print(f"Theoretical pieces needed: {theoretical_pieces_needed} (4 cells each)")
    
    # Create inventory with 25 pieces - exactly what's needed for complete solution
    inventory = {'pieces': {}}
    piece_count = 0
    
    # Use first 25 piece types (A-Y covers 25 pieces)
    for piece_id in 'ABCDEFGHIJKLMNOPQRSTUVWXY':
        if piece_id in pieces and piece_count < 25:
            inventory['pieces'][piece_id] = 1
            piece_count += 1
    
    print(f"Inventory: {sum(inventory['pieces'].values())} pieces")
    print(f"Piece types: {', '.join(sorted(inventory['pieces'].keys()))}")
    
    engine = EngineCAdapter()
    
    # Short test with good progress reporting
    options = {
        'seed': 20250907,
        'max_results': 1,
        'progress_interval_ms': 2000,  # Progress every 2 seconds
        'flags': {
            'time_budget_s': 30.0,  # 30 second test
            'pruning_level': 'basic',
            'shuffle': 'ties_only'
        }
    }
    
    print(f"\nRunning Engine-C for {options['flags']['time_budget_s']} seconds...")
    print("Looking for complete solution or maximum depth reached...")
    
    start_time = time.time()
    max_depth = 0
    nodes_explored = 0
    progress_count = 0
    
    try:
        for event in engine.solve(container, inventory, pieces, options):
            
            if event['type'] == 'tick':
                progress_count += 1
                metrics = event['metrics']
                elapsed = time.time() - start_time
                
                nodes_explored = metrics.get('nodes', 0)
                depth = metrics.get('depth', 0)
                max_depth = max(max_depth, depth)
                pruned = metrics.get('pruned', 0)
                solutions = metrics.get('solutions', 0)
                
                # Calculate progress percentage
                depth_progress = (depth / 25) * 100 if depth > 0 else 0
                
                print(f"[{elapsed:5.1f}s] Nodes: {nodes_explored:6d} | "
                      f"Depth: {depth:2d}/25 ({depth_progress:4.1f}%) | "
                      f"Pruned: {pruned:6d} | Solutions: {solutions}")
                
            elif event['type'] == 'solution':
                solution = event['solution']
                placements = solution.get('placements', [])
                elapsed = time.time() - start_time
                
                print(f"\n*** COMPLETE SOLUTION FOUND in {elapsed:.1f}s! ***")
                print(f"Pieces placed: {len(placements)}")
                print(f"Cells covered: {len(placements) * 4}")
                print(f"Container coverage: {(len(placements) * 4 / total_cells) * 100:.1f}%")
                
                # Show piece usage
                pieces_used = {}
                for placement in placements:
                    piece_id = placement['piece']
                    pieces_used[piece_id] = pieces_used.get(piece_id, 0) + 1
                
                if pieces_used:
                    usage_str = ', '.join([f'{k}={v}' for k, v in sorted(pieces_used.items())])
                    print(f"Pieces used: {usage_str}")
                
                if len(placements) == 25:
                    print("*** PERFECT SOLUTION - ALL 25 PIECES PLACED! ***")
                
            elif event['type'] == 'done':
                elapsed = time.time() - start_time
                metrics = event['metrics']
                
                print(f"\n=== SEARCH COMPLETED ===")
                print(f"Time: {elapsed:.2f}s")
                print(f"Nodes explored: {metrics.get('nodes', 0):,}")
                print(f"Nodes pruned: {metrics.get('pruned', 0):,}")
                print(f"Max depth reached: {metrics.get('bestDepth', max_depth)}")
                print(f"Solutions found: {metrics.get('solutions', 0)}")
                print(f"Progress reports: {progress_count}")
                
                if metrics.get('nodes', 0) > 0:
                    print(f"Search rate: {metrics.get('nodes', 0)/elapsed:,.0f} nodes/s")
                
                # Analysis
                final_depth = metrics.get('bestDepth', max_depth)
                if metrics.get('solutions', 0) > 0:
                    print("*** COMPLETE SOLUTION ACHIEVED! ***")
                else:
                    cells_placed = final_depth * 4
                    coverage = (cells_placed / total_cells) * 100
                    print(f"*** PARTIAL SOLUTION ***")
                    print(f"Placed {final_depth} pieces covering {cells_placed} cells ({coverage:.1f}%)")
                    print(f"Remaining: {25 - final_depth} pieces, {total_cells - cells_placed} cells")
                
                break
                
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n*** ERROR: {e} ***")
        print(f"Ran for {elapsed:.1f}s, explored {nodes_explored:,} nodes, reached depth {max_depth}")

if __name__ == '__main__':
    main()
