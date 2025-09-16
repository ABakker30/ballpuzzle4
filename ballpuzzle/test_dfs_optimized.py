#!/usr/bin/env python3

from src.solver.engines.dfs_engine import DFSEngine
from src.io.container import load_container
import time

def test_dfs_optimized():
    # Load 16-cell container
    container = load_container('data/containers/legacy_fixed/16 cell container.json')
    print(f'Container: {len(container["coordinates"])} cells')
    
    # Test with all 25 pieces (A-Y) with 1 each
    inventory = {'pieces': {chr(65+i): 1 for i in range(25)}}
    
    print('\n=== DFS Engine Optimized Test: 10 seconds, max 10 solutions ===')
    
    engine = DFSEngine()
    options = {
        'time_limit': 10,           # 10 seconds as requested
        'seed': 42,                 # Fixed seed for reproducibility
        'max_results': 10,          # 10 solution cap as requested
        'mrv': True,                # Use enhanced MRV heuristic
        'support': True,            # Use support bias
        'candidate_limit': 20,      # Limit candidates per node for speed
        'prefer_small_pieces': True # Prioritize smaller pieces
    }
    
    start_wall_time = time.time()
    solutions = 0
    first_solution_time = None
    
    for event in engine.solve(container, inventory, None, options):
        if event['type'] == 'solution':
            solutions += 1
            solution_time = event.get('t_ms', 0) / 1000.0
            
            if first_solution_time is None:
                first_solution_time = solution_time
                print(f'First solution found at {solution_time:.2f}s')
            
            # Show each solution found
            pieces_used = event['solution']['piecesUsed']
            total_pieces = sum(pieces_used.values())
            print(f'Solution {solutions}: {total_pieces} pieces used at {solution_time:.2f}s')
            
        elif event['type'] == 'done':
            final_time = event.get('t_ms', 0) / 1000.0
            wall_time = time.time() - start_wall_time
            nodes = event.get('metrics', {}).get('nodes', 0)
            
            print(f'\nOPTIMIZED DFS RESULTS:')
            print(f'  Solutions found: {solutions}')
            print(f'  Engine time: {final_time:.2f}s')
            print(f'  Wall time: {wall_time:.2f}s')
            print(f'  Nodes explored: {nodes:,}')
            
            if solutions > 0 and final_time > 0:
                throughput = solutions / final_time
                print(f'  Throughput: {throughput:.1f} solutions/second')
            
            # Check termination reason
            if solutions >= 10:
                print(f'  Termination: Solution limit reached ({solutions}/10)')
            elif final_time >= 10:
                print(f'  Termination: Time limit reached ({final_time:.1f}s/10s)')
            else:
                print(f'  Termination: Search completed')
            break

if __name__ == '__main__':
    test_dfs_optimized()
