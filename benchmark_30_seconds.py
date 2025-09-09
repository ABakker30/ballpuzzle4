#!/usr/bin/env python3

from src.solver.engines.dfs_engine import DFSEngine
from src.solver.engines.dlx_engine import DLXEngine
from src.io.container import load_container
import time

def benchmark_engines():
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
        last_solution_time = None
        
        try:
            for event in engine.solve(container, inventory, None, options):
                if event['type'] == 'solution':
                    solutions += 1
                    solution_time = event.get('t_ms', 0) / 1000.0
                    
                    if first_solution_time is None:
                        first_solution_time = solution_time
                        print(f'  First solution found at {solution_time:.2f}s')
                    
                    last_solution_time = solution_time
                    
                    # Show progress every 10 solutions
                    if solutions % 10 == 0:
                        print(f'  {solutions} solutions found at {solution_time:.2f}s')
                        
                elif event['type'] == 'done':
                    final_time = event.get('t_ms', 0) / 1000.0
                    wall_time = time.time() - start_wall_time
                    nodes = event.get('metrics', {}).get('nodes', 0)
                    
                    print(f'  Final: {solutions} solutions in {final_time:.2f}s (wall: {wall_time:.2f}s)')
                    if nodes > 0:
                        print(f'  Nodes explored: {nodes:,}')
                    
                    results[engine_name] = {
                        'solutions': solutions,
                        'engine_time': final_time,
                        'wall_time': wall_time,
                        'first_solution': first_solution_time,
                        'last_solution': last_solution_time,
                        'nodes': nodes
                    }
                    break
                    
        except Exception as e:
            print(f'  Error: {e}')
            wall_time = time.time() - start_wall_time
            results[engine_name] = {
                'solutions': solutions,
                'engine_time': wall_time,
                'wall_time': wall_time,
                'first_solution': first_solution_time,
                'last_solution': last_solution_time,
                'nodes': 0,
                'error': str(e)
            }
    
    # Summary comparison
    print('\n=== Performance Summary ===')
    for engine_name, data in results.items():
        solutions = data['solutions']
        engine_time = data['engine_time']
        wall_time = data['wall_time']
        
        print(f'\n{engine_name} Engine:')
        print(f'  Solutions found: {solutions}')
        print(f'  Engine time: {engine_time:.2f}s')
        print(f'  Wall time: {wall_time:.2f}s')
        
        if solutions > 0 and engine_time > 0:
            throughput = solutions / engine_time
            print(f'  Throughput: {throughput:.1f} solutions/second')
        
        if data.get('first_solution'):
            print(f'  Time to first solution: {data["first_solution"]:.2f}s')
        
        if data.get('nodes', 0) > 0:
            print(f'  Search nodes: {data["nodes"]:,}')
        
        if 'error' in data:
            print(f'  Error: {data["error"]}')
    
    # Winner determination
    if len(results) == 2:
        dfs_solutions = results.get('DFS', {}).get('solutions', 0)
        dlx_solutions = results.get('DLX', {}).get('solutions', 0)
        
        print(f'\n=== Winner ===')
        if dfs_solutions > dlx_solutions:
            print(f'DFS wins with {dfs_solutions} vs {dlx_solutions} solutions')
        elif dlx_solutions > dfs_solutions:
            print(f'DLX wins with {dlx_solutions} vs {dfs_solutions} solutions')
        else:
            print(f'Tie: both engines found {dfs_solutions} solutions')

if __name__ == '__main__':
    benchmark_engines()
