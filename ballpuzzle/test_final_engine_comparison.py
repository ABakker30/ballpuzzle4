#!/usr/bin/env python3

from src.solver.engines.dfs_engine import DFSEngine
from src.solver.engines.dlx_engine import DLXEngine
from src.io.container import load_container
import time

def test_final_engine_comparison():
    # Load container
    container = load_container('data/containers/legacy_fixed/16 cell container.json')
    print(f'Container loaded: {len(container["coordinates"])} cells')

    # Test both engines with standardized parameters
    inventory = {'pieces': {chr(65+i): 1 for i in range(25)}}  # A-Y = 1 each
    
    print('\n=== Engine Comparison: 60-second time limit, max 1000 solutions ===')
    
    for engine_name, engine_class in [('DFS', DFSEngine), ('DLX', DLXEngine)]:
        print(f'\n{engine_name} Engine:')
        engine = engine_class()
        options = {'time_limit': 60, 'seed': 1, 'max_results': 1000}
        
        start_wall_time = time.time()
        solutions = 0
        
        for event in engine.solve(container, inventory, None, options):
            if event['type'] == 'solution':
                solutions += 1
                if solutions <= 3:  # Show first 3 solutions
                    pieces_used = event['solution']['piecesUsed']
                    total_pieces = sum(pieces_used.values())
                    elapsed = event.get('t_ms', 0) / 1000.0
                    print(f'  Solution {solutions}: {total_pieces} pieces at {elapsed:.2f}s')
            elif event['type'] == 'done':
                elapsed = event.get('t_ms', 0) / 1000.0
                wall_elapsed = time.time() - start_wall_time
                nodes = event.get('metrics', {}).get('nodes', 0)
                print(f'  Final: {solutions} solutions in {elapsed:.2f}s (wall: {wall_elapsed:.2f}s)')
                if nodes > 0:
                    print(f'  Nodes explored: {nodes}')
                if solutions > 0 and elapsed > 0:
                    print(f'  Throughput: {solutions/elapsed:.1f} solutions/second')
                break

if __name__ == '__main__':
    test_final_engine_comparison()
