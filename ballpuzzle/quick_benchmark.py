#!/usr/bin/env python3

from src.solver.engines.dfs_engine import DFSEngine
from src.solver.engines.dlx_engine import DLXEngine
from src.io.container import load_container
import time

def quick_benchmark():
    # Load 16-cell container
    container = load_container('data/containers/legacy_fixed/16 cell container.json')
    print(f'Container: {len(container["coordinates"])} cells')
    
    # Standard inventory: all 25 pieces (A-Y) with 1 each
    inventory = {'pieces': {chr(65+i): 1 for i in range(25)}}
    
    print('\n=== 30-Second Engine Performance Comparison ===')
    
    results = {}
    
    for engine_name, engine_class in [('DFS', DFSEngine), ('DLX', DLXEngine)]:
        print(f'\n{engine_name} Engine Test:')
        engine = engine_class()
        options = {
            'time_limit': 30,  # 30 seconds
            'seed': 42,        # Fixed seed for reproducibility
            'max_results': 10000  # High limit to test time constraint
        }
        
        start_wall_time = time.time()
        solutions = 0
        first_solution_time = None
        
        try:
            for event in engine.solve(container, inventory, None, options):
                if event['type'] == 'solution':
                    solutions += 1
                    solution_time = event.get('t_ms', 0) / 1000.0
                    
                    if first_solution_time is None:
                        first_solution_time = solution_time
                        print(f'  First solution at {solution_time:.2f}s')
                    
                    # Show progress for DFS every solution, DLX every 100
                    if engine_name == 'DFS' or solutions % 100 == 0:
                        print(f'  {solutions} solutions at {solution_time:.2f}s')
                        
                elif event['type'] == 'done':
                    final_time = event.get('t_ms', 0) / 1000.0
                    wall_time = time.time() - start_wall_time
                    nodes = event.get('metrics', {}).get('nodes', 0)
                    
                    print(f'  FINAL: {solutions} solutions in {final_time:.2f}s')
                    
                    results[engine_name] = {
                        'solutions': solutions,
                        'time': final_time,
                        'nodes': nodes
                    }
                    break
                    
        except Exception as e:
            wall_time = time.time() - start_wall_time
            print(f'  ERROR after {solutions} solutions in {wall_time:.2f}s: {e}')
            results[engine_name] = {
                'solutions': solutions,
                'time': wall_time,
                'nodes': 0,
                'error': True
            }
    
    # Results
    print(f'\n=== RESULTS ===')
    for name, data in results.items():
        solutions = data['solutions']
        time_taken = data['time']
        throughput = solutions / time_taken if time_taken > 0 else 0
        
        print(f'{name}: {solutions} solutions in {time_taken:.2f}s ({throughput:.1f}/sec)')
        if data.get('nodes', 0) > 0:
            print(f'     {data["nodes"]:,} nodes explored')
    
    # Winner
    if 'DFS' in results and 'DLX' in results:
        dfs_count = results['DFS']['solutions']
        dlx_count = results['DLX']['solutions']
        print(f'\nWINNER: {"DLX" if dlx_count > dfs_count else "DFS" if dfs_count > dlx_count else "TIE"}')
        print(f'DFS: {dfs_count} vs DLX: {dlx_count}')

if __name__ == '__main__':
    quick_benchmark()
