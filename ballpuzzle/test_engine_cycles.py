#!/usr/bin/env python3
"""Test engines with cycle-based limits and progress reporting."""

from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.solver.engines.dfs_engine import DFSEngine
from src.solver.engines.dlx_engine import DLXEngine
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
import time

def test_engine_cycles(engine_name: str, max_nodes: int = 1000, progress_every: int = 200):
    """Test engine with node-based limits and regular progress reporting."""
    
    print(f"\n=== Testing {engine_name.upper()} Engine (Max {max_nodes} nodes) ===")
    
    # Load Shape_3 container
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    
    # Reasonable inventory for testing
    inventory = {'pieces': {}}
    for piece_id in 'ABCDEFGH':  # 8 piece types
        if piece_id in pieces:
            inventory['pieces'][piece_id] = 2  # 2 of each
    
    print(f"Container: {len(container['coordinates'])} cells")
    print(f"Inventory: {sum(inventory['pieces'].values())} pieces")
    print(f"Will stop after {max_nodes} nodes or when solution found")
    
    # Select engine
    engines = {
        'engine-c': EngineCAdapter(),
        'dfs': DFSEngine(),
        'dlx': DLXEngine()
    }
    
    if engine_name not in engines:
        print(f"Unknown engine: {engine_name}")
        return
        
    engine = engines[engine_name]
    
    # Configure options with node limit
    options = {
        'seed': 20250907,
        'max_results': 1,
        'progress_interval_ms': 1000,  # Progress every 1 second
        'caps': {
            'maxNodes': max_nodes  # Node limit
        },
        'flags': {
            'time_budget_s': 120.0,  # Fallback time limit
            'pruning_level': 'basic',
            'shuffle': 'ties_only'
        }
    }
    
    # Run engine with progress tracking
    start_time = time.time()
    nodes_explored = 0
    max_depth = 0
    progress_reports = 0
    solutions_found = 0
    
    print(f"\nStarting {engine_name} search...")
    print("Progress reports every ~1 second:")
    
    try:
        for event in engine.solve(container, inventory, pieces, options):
            
            if event['type'] == 'tick':
                progress_reports += 1
                metrics = event['metrics']
                elapsed = time.time() - start_time
                
                nodes_explored = metrics.get('nodes', 0)
                depth = metrics.get('depth', 0)
                max_depth = max(max_depth, depth)
                pruned = metrics.get('pruned', 0)
                
                # Progress report
                print(f"[{elapsed:5.1f}s] Nodes: {nodes_explored:4d}/{max_nodes} | "
                      f"Depth: {depth:2d} | Pruned: {pruned:4d} | "
                      f"Rate: {nodes_explored/elapsed:.0f} nodes/s")
                
                # Check if we're approaching limit
                if nodes_explored >= max_nodes * 0.9:
                    print(f"Approaching node limit ({nodes_explored}/{max_nodes})")
                    
            elif event['type'] == 'solution':
                solutions_found += 1
                solution = event['solution']
                placements = solution.get('placements', [])
                
                print(f"\n*** SOLUTION FOUND! ***")
                print(f"Pieces placed: {len(placements)}")
                print(f"Cells covered: {len(placements) * 4}")
                
                # Show piece usage
                pieces_used = {}
                for placement in placements:
                    piece_id = placement['piece']
                    pieces_used[piece_id] = pieces_used.get(piece_id, 0) + 1
                
                if pieces_used:
                    usage_str = ', '.join([f'{k}={v}' for k, v in sorted(pieces_used.items())])
                    print(f"Pieces used: {usage_str}")
                
            elif event['type'] == 'done':
                elapsed = time.time() - start_time
                metrics = event['metrics']
                
                print(f"\n=== {engine_name.upper()} COMPLETED ===")
                print(f"Time: {elapsed:.2f}s")
                print(f"Nodes explored: {metrics.get('nodes', 0)}")
                print(f"Nodes pruned: {metrics.get('pruned', 0)}")
                print(f"Max depth reached: {metrics.get('bestDepth', max_depth)}")
                print(f"Solutions found: {metrics.get('solutions', 0)}")
                print(f"Progress reports: {progress_reports}")
                print(f"Search rate: {metrics.get('nodes', 0)/elapsed:.0f} nodes/s")
                
                # Analysis
                final_depth = metrics.get('bestDepth', max_depth)
                if metrics.get('solutions', 0) > 0:
                    print("*** COMPLETE SOLUTION ACHIEVED! ***")
                elif metrics.get('nodes', 0) >= max_nodes:
                    print(f"*** STOPPED AT NODE LIMIT ({max_nodes}) ***")
                    print(f"Reached depth {final_depth} - placed {final_depth} pieces")
                else:
                    print(f"Search exhausted at depth {final_depth}")
                
                break
                
    except Exception as e:
        print(f"\n*** ERROR: {e} ***")
        elapsed = time.time() - start_time
        print(f"Ran for {elapsed:.1f}s, explored {nodes_explored} nodes")

def main():
    """Test different engines with cycle limits."""
    
    print("=== Engine Cycle Testing ===")
    print("Tests engines with node limits to prevent lockups")
    
    # Test configurations
    tests = [
        ('engine-c', 500, 100),   # Engine-C: 500 nodes, report every 100
        ('engine-c', 2000, 400),  # Engine-C: 2000 nodes, report every 400
        ('dfs', 500, 100),        # DFS comparison: 500 nodes
        ('dlx', 200, 50),         # DLX: smaller limit due to different metrics
    ]
    
    for engine_name, max_nodes, progress_every in tests:
        test_engine_cycles(engine_name, max_nodes, progress_every)
        
        # Pause between tests
        print("\n" + "="*60)
        input("Press Enter to continue to next test...")
    
    print("\n=== All Engine Tests Complete ===")

if __name__ == '__main__':
    main()
