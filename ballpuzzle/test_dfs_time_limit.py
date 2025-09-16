#!/usr/bin/env python3

from src.solver.engines.dfs_engine import DFSEngine
from src.io.container import load_container
import json

def test_dfs_time_limit():
    # Load container
    container = load_container('data/containers/legacy_fixed/16 cell container.json')
    print(f'Container loaded: {len(container["coordinates"])} cells')

    # Test engine
    engine = DFSEngine()
    inventory = {'pieces': {chr(65+i): 1 for i in range(25)}}  # A-Y = 1 each
    options = {'time_limit': 10, 'seed': 1, 'max_results': 10000}

    print('Starting DFS engine test with 10-second time limit...')
    solutions = 0
    start_time = None
    for event in engine.solve(container, inventory, None, options):
        if start_time is None:
            start_time = event['t_ms']
        
        if event['type'] == 'solution':
            solutions += 1
            elapsed = (event['t_ms'] - start_time) / 1000.0
            print(f'Solution {solutions} found at {elapsed:.2f}s')
            # Print piece usage for first few solutions
            if solutions <= 3:
                pieces_used = event['solution']['piecesUsed']
                used_pieces = [k for k, v in pieces_used.items() if v > 0]
                print(f'  Pieces used: {used_pieces}')
        elif event['type'] == 'done':
            elapsed = (event['t_ms'] - start_time) / 1000.0
            print(f'Done: {solutions} solutions, {event["metrics"]["nodes"]} nodes, {elapsed:.2f}s elapsed')
            if elapsed > 0:
                print(f'Performance: {solutions/elapsed:.1f} solutions/second')
            else:
                print(f'Performance: {solutions} solutions in <0.01s')
            break

if __name__ == '__main__':
    test_dfs_time_limit()
