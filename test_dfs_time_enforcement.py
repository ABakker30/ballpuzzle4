#!/usr/bin/env python3

from src.solver.engines.dfs_engine import DFSEngine
from src.io.container import load_container
import time

def test_dfs_time_enforcement():
    # Load a larger container that will take more time to solve
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    print(f'Container loaded: {len(container["coordinates"])} cells')

    # Test DFS engine with short time limits to force timeout
    inventory = {'pieces': {chr(65+i): 1 for i in range(25)}}  # A-Y = 1 each
    
    time_limits = [2, 5, 10]  # Short time limits to test enforcement
    
    for time_limit in time_limits:
        print(f'\n=== Testing DFS with {time_limit}s time limit on 100-cell container ===')
        engine = DFSEngine()
        options = {'time_limit': time_limit, 'seed': 1, 'max_results': 10000}
        
        start_wall_time = time.time()
        solutions = 0
        nodes = 0
        
        for event in engine.solve(container, inventory, None, options):
            if event['type'] == 'solution':
                solutions += 1
                elapsed = (event['t_ms']) / 1000.0
                print(f'  Solution {solutions} found at {elapsed:.2f}s')
            elif event['type'] == 'done':
                elapsed = (event['t_ms']) / 1000.0
                wall_elapsed = time.time() - start_wall_time
                nodes = event['metrics']['nodes']
                print(f'  Done: {solutions} solutions, {nodes} nodes')
                print(f'  Engine time: {elapsed:.2f}s, Wall time: {wall_elapsed:.2f}s')
                
                # Check if time limit was enforced (allowing 0.5s tolerance)
                if elapsed >= time_limit - 0.5:
                    print(f'  Time limit enforcement: YES (stopped at {elapsed:.2f}s)')
                else:
                    print(f'  Time limit enforcement: NO (finished early at {elapsed:.2f}s)')
                break

if __name__ == '__main__':
    test_dfs_time_enforcement()
