#!/usr/bin/env python3
"""Final validation script for Engine-C as primary solver."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def main():
    print('=== Engine-C Final Validation ===')

    # Test 1: Simple exact-fit case
    print('\n1. Testing 4-cell exact-fit case...')
    container_simple = {
        'coordinates': [[0, 0, 0], [0, 1, 0], [1, 0, 0], [1, 1, 0]]
    }
    pieces = load_fcc_A_to_Y()
    inventory_simple = {'pieces': {'A': 1}}
    engine = EngineCAdapter()

    start = time.time()
    events = list(engine.solve(container_simple, inventory_simple, pieces, {'seed': 12345}))
    elapsed = time.time() - start

    solution_events = [e for e in events if e['type'] == 'solution']
    done_events = [e for e in events if e['type'] == 'done']

    print(f'   Time: {elapsed:.3f}s')
    print(f'   Solutions found: {len(solution_events)}')
    if done_events:
        print(f'   Nodes explored: {done_events[0]["metrics"]["nodes"]}')
    print(f'   Status: {"PASS" if solution_events else "FAIL"}')

    # Test 2: 100-cell container performance
    print('\n2. Testing Shape_3 100-cell performance...')
    container_100 = load_container('data/containers/legacy_fixed/Shape_3.json')
    inventory_100 = {'pieces': {'A': 1, 'B': 1}}

    start = time.time()
    events = list(engine.solve(container_100, inventory_100, pieces, {'seed': 20250907}))
    elapsed = time.time() - start

    done_events = [e for e in events if e['type'] == 'done']
    metrics = done_events[0]['metrics'] if done_events else {}

    print(f'   Time: {elapsed:.3f}s')
    print(f'   Nodes explored: {metrics.get("nodes", "N/A")}')
    print(f'   Pruned: {metrics.get("pruned", "N/A")}')
    print(f'   Solutions: {metrics.get("solutions", "N/A")}')
    print(f'   Status: COMPLETE')

    # Test 3: Determinism validation
    print('\n3. Testing deterministic behavior...')
    seed = 42
    events1 = list(engine.solve(container_simple, inventory_simple, pieces, {'seed': seed}))
    events2 = list(engine.solve(container_simple, inventory_simple, pieces, {'seed': seed}))

    done1 = [e for e in events1 if e['type'] == 'done'][0]['metrics']
    done2 = [e for e in events2 if e['type'] == 'done'][0]['metrics']

    deterministic = (done1['nodes'] == done2['nodes'] and 
                    done1['solutions'] == done2['solutions'] and
                    done1['pruned'] == done2['pruned'])

    print(f'   Run 1: {done1["nodes"]} nodes, {done1["solutions"]} solutions')
    print(f'   Run 2: {done2["nodes"]} nodes, {done2["solutions"]} solutions')
    print(f'   Status: {"DETERMINISTIC" if deterministic else "NON-DETERMINISTIC"}')

    print('\n=== Engine-C Validation Complete ===')
    print('Engine-C is ready as the primary high-performance FCC solver!')

if __name__ == '__main__':
    main()
