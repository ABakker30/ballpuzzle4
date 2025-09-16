#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from solver.engines.dfs_engine import DFSEngine
from data.containers import load_container_by_name

def test_dfs_combinations():
    """Test DFS engine with piece combination enumeration approach."""
    
    # Load 16-cell container
    container = load_container_by_name("Shape_10")
    print(f"Container: {container['name']} ({len(container['coordinates'])} cells)")
    
    # Set up inventory (all 25 pieces with 1 each)
    inventory = {chr(ord('A') + i): 1 for i in range(25)}
    print(f"Inventory: {len(inventory)} pieces (A-Y = 1 each)")
    
    # Test DFS engine with 10-second time limit and 10 solution cap
    engine = DFSEngine()
    options = {
        "time_limit": 10,
        "max_results": 10,
        "progress_interval_ms": 1000
    }
    
    print("\n=== Testing DFS Engine with Combination Enumeration ===")
    print(f"Time limit: {options['time_limit']} seconds")
    print(f"Solution cap: {options['max_results']} solutions")
    print()
    
    solutions_found = 0
    start_time = None
    
    try:
        for event in engine.solve(container, inventory, {}, options):
            if event["type"] == "solution":
                solutions_found += 1
                if start_time is None:
                    start_time = event["t_ms"]
                
                solution = event["solution"]
                pieces_used = solution["piecesUsed"]
                total_pieces = sum(pieces_used.values())
                
                print(f"Solution {solutions_found}: {total_pieces} pieces used")
                print(f"  Pieces: {pieces_used}")
                print(f"  Time: {event['t_ms']}ms")
                print()
                
            elif event["type"] == "done":
                metrics = event["metrics"]
                print(f"=== DFS Engine Complete ===")
                print(f"Solutions found: {metrics['solutions']}")
                print(f"Total time: {event['t_ms']}ms")
                print(f"Nodes explored: {metrics.get('nodes', 'N/A')}")
                print(f"Best depth: {metrics.get('bestDepth', 'N/A')}")
                
                if solutions_found > 0:
                    print(f"First solution at: {start_time}ms")
                    throughput = solutions_found / (event['t_ms'] / 1000.0) if event['t_ms'] > 0 else 0
                    print(f"Throughput: {throughput:.2f} solutions/second")
                
                break
                
    except Exception as e:
        print(f"Error during DFS execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dfs_combinations()
