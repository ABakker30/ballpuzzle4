#!/usr/bin/env python3

from src.solver.engines.dfs_engine import DFSEngine
from src.solver.engines.dlx_engine import DLXEngine
from src.io.container import load_container
import json

def test_engine_comparison():
    # Load container
    container = load_container('data/containers/legacy_fixed/16 cell container.json')
    print(f'Container loaded: {len(container["coordinates"])} cells')

    # Test both engines
    inventory = {'pieces': {chr(65+i): 1 for i in range(25)}}  # A-Y = 1 each
    
    print('\n=== DFS Engine Test ===')
    engine_dfs = DFSEngine()
    options_dfs = {'time_limit': 60, 'seed': 1, 'max_results': 1000}
    
    solutions_dfs = 0
    for event in engine_dfs.solve(container, inventory, None, options_dfs):
        if event['type'] == 'solution':
            solutions_dfs += 1
            pieces_used = event['solution']['piecesUsed']
            used_pieces = [k for k, v in pieces_used.items() if v > 0]
            total_pieces = sum(pieces_used.values())
            print(f'DFS Solution {solutions_dfs}: {total_pieces} pieces used: {used_pieces}')
        elif event['type'] == 'done':
            elapsed = event['t_ms'] / 1000.0
            print(f'DFS Done: {solutions_dfs} solutions, {event["metrics"]["nodes"]} nodes, {elapsed:.2f}s')
            break
    
    print('\n=== DLX Engine Test ===')
    engine_dlx = DLXEngine()
    options_dlx = {'time_limit': 60, 'seed': 1, 'max_results': 1000}
    
    solutions_dlx = 0
    for event in engine_dlx.solve(container, inventory, None, options_dlx):
        if event['type'] == 'solution':
            solutions_dlx += 1
            pieces_used = event['solution']['piecesUsed']
            used_pieces = [k for k, v in pieces_used.items() if v > 0]
            total_pieces = sum(pieces_used.values())
            print(f'DLX Solution {solutions_dlx}: {total_pieces} pieces used: {used_pieces}')
        elif event['type'] == 'done':
            elapsed = event['t_ms'] / 1000.0
            print(f'DLX Done: {solutions_dlx} solutions, {elapsed:.2f}s')
            break
    
    print(f'\n=== Comparison ===')
    print(f'DFS: {solutions_dfs} solutions')
    print(f'DLX: {solutions_dlx} solutions')

if __name__ == '__main__':
    test_engine_comparison()
