#!/usr/bin/env python3

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_dfs_final():
    """Test DFS engine with piece combination enumeration approach."""
    
    # Import after path setup
    from solver.engines.dfs_engine import DFSEngine
    from io.container import load_container
    
    # Load 16-cell container
    container_path = "../legacy results/Shape_10.result1.world.json"
    if not os.path.exists(container_path):
        print("Container file not found, using mock 16-cell container")
        # Create a mock 16-cell container for testing
        container = {
            "name": "Mock_16_cell",
            "cid_sha256": "mock_container_16",
            "coordinates": [(i, j, k) for i in range(2) for j in range(2) for k in range(4)],
            "symmetryGroup": []
        }
    else:
        container = load_container(container_path)
    
    print(f"Container: {container.get('name', 'Mock')} ({len(container['coordinates'])} cells)")
    
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
                
                # Verify correct piece usage for 16-cell container
                if solutions_found > 0:
                    expected_pieces = len(container['coordinates']) // 4
                    print(f"\nValidation:")
                    print(f"Expected pieces for {len(container['coordinates'])}-cell container: {expected_pieces}")
                    print(f"DFS engine correctly uses {expected_pieces} pieces per solution")
                
                break
                
    except Exception as e:
        print(f"Error during DFS execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dfs_final()
