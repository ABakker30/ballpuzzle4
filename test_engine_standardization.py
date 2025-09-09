#!/usr/bin/env python3

from src.solver.engines.dfs_engine import DFSEngine
from src.solver.engines.dlx_engine import DLXEngine
from src.io.container import load_container
import time

def test_engine_standardization():
    # Load container
    container = load_container('data/containers/legacy_fixed/16 cell container.json')
    print(f'Container loaded: {len(container["coordinates"])} cells')

    # Test both engines with standardized parameters
    inventory = {'pieces': {chr(65+i): 1 for i in range(25)}}  # A-Y = 1 each
    
    # Test 1: Time limit enforcement (30 seconds, unlimited solutions)
    print('\n=== Test 1: Time Limit Enforcement (30s) ===')
    
    for engine_name, engine_class in [('DFS', DFSEngine), ('DLX', DLXEngine)]:
        print(f'\n{engine_name} Engine:')
        engine = engine_class()
        options = {'time_limit': 30, 'seed': 1, 'max_results': 10000}
        
        start_wall_time = time.time()
        solutions = 0
        
        try:
            for event in engine.solve(container, inventory, None, options):
                if event['type'] == 'solution':
                    solutions += 1
                    elapsed = event.get('t_ms', 0) / 1000.0
                    if solutions <= 5:  # Show first 5 solutions
                        pieces_used = event['solution']['piecesUsed']
                        total_pieces = sum(pieces_used.values())
                        print(f'  Solution {solutions}: {total_pieces} pieces at {elapsed:.2f}s')
                elif event['type'] == 'done':
                    elapsed = event.get('t_ms', 0) / 1000.0
                    wall_elapsed = time.time() - start_wall_time
                    print(f'  Done: {solutions} solutions in {elapsed:.2f}s (wall: {wall_elapsed:.2f}s)')
                    
                    # Check termination reason
                    if elapsed >= 29.5:  # Allow 0.5s tolerance
                        print(f'  Termination: TIME LIMIT (expected)')
                    elif solutions >= 10000:
                        print(f'  Termination: SOLUTION LIMIT (expected)')
                    else:
                        print(f'  Termination: SEARCH EXHAUSTED (natural)')
                    break
        except StopIteration as e:
            elapsed = time.time() - start_wall_time
            print(f'  Stopped: {solutions} solutions in {elapsed:.2f}s - {e}')
    
    # Test 2: Solution count limit (5 solutions, unlimited time)
    print('\n=== Test 2: Solution Count Limit (5 solutions) ===')
    
    for engine_name, engine_class in [('DFS', DFSEngine), ('DLX', DLXEngine)]:
        print(f'\n{engine_name} Engine:')
        engine = engine_class()
        options = {'time_limit': 0, 'seed': 1, 'max_results': 5}
        
        start_wall_time = time.time()
        solutions = 0
        
        try:
            for event in engine.solve(container, inventory, None, options):
                if event['type'] == 'solution':
                    solutions += 1
                    elapsed = event.get('t_ms', 0) / 1000.0
                    pieces_used = event['solution']['piecesUsed']
                    total_pieces = sum(pieces_used.values())
                    print(f'  Solution {solutions}: {total_pieces} pieces at {elapsed:.2f}s')
                elif event['type'] == 'done':
                    elapsed = event.get('t_ms', 0) / 1000.0
                    wall_elapsed = time.time() - start_wall_time
                    print(f'  Done: {solutions} solutions in {elapsed:.2f}s (wall: {wall_elapsed:.2f}s)')
                    
                    # Check termination reason
                    if solutions >= 5:
                        print(f'  Termination: SOLUTION LIMIT (expected)')
                    else:
                        print(f'  Termination: SEARCH EXHAUSTED (natural)')
                    break
        except StopIteration as e:
            elapsed = time.time() - start_wall_time
            print(f'  Stopped: {solutions} solutions in {elapsed:.2f}s - {e}')

if __name__ == '__main__':
    test_engine_standardization()
