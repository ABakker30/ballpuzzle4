#!/usr/bin/env python3

import sys
import os
import time

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Direct imports to bypass CLI issues
from solver.engines.dfs_engine import DFSEngine
from io.container import load_container

def main():
    # Load the 40 cell container
    container = load_container('data/containers/v1/40 cell.fcc.json')
    
    # Set up inventory and options
    inventory = {'A': 3, 'E': 3, 'T': 2, 'Y': 2}
    options = {
        'max_results': 20,
        'time_limit': 10,
        'seed': 42
    }
    
    print('Running DFS engine with 40 cell container...')
    print('Inventory: A=3, E=3, T=2, Y=2')
    print('Target: 20 solutions in 10 seconds')
    print()
    
    # Create DFS engine directly
    engine = DFSEngine()
    solutions_found = 0
    start_time = time.time()
    
    try:
        for event in engine.solve(container, inventory, options):
            if event.get('type') == 'solution':
                solutions_found += 1
                elapsed = time.time() - start_time
                print(f'Solution {solutions_found} found in {elapsed:.2f}s')
                
                if solutions_found >= 20:
                    break
            elif event.get('type') == 'done':
                break
                
    except Exception as e:
        print(f'Error during solve: {e}')
        import traceback
        traceback.print_exc()
    
    elapsed = time.time() - start_time
    print(f'\nCompleted: {solutions_found} solutions found in {elapsed:.2f} seconds')
    
    if solutions_found >= 20:
        print('SUCCESS: Found 20 solutions within time limit!')
    else:
        print(f'PARTIAL: Found {solutions_found} solutions in {elapsed:.2f}s')

if __name__ == '__main__':
    main()
