#!/usr/bin/env python3
"""Direct test of DFS engine with 40 cell container."""

import sys
import os
import json
import time

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from solver.engines.dfs_engine import DFSEngine

def main():
    # Load container
    container_path = "data/containers/v1/40 cell.fcc.json"
    with open(container_path, 'r') as f:
        container = json.load(f)
    
    # Set up inventory and options
    inventory = {"A": 3, "E": 3, "T": 2, "Y": 2}
    options = {
        "max_results": 20,
        "time_limit": 10,
        "seed": 42
    }
    
    print("Running DFS engine with 40 cell container...")
    print("Inventory: A=3, E=3, T=2, Y=2")
    print("Target: 20 solutions in 10 seconds")
    print()
    
    # Create engine and solve
    engine = DFSEngine()
    solutions_found = 0
    start_time = time.time()
    
    try:
        for event in engine.solve(container, inventory, options):
            if event.get("type") == "solution":
                solutions_found += 1
                elapsed = time.time() - start_time
                print(f"Solution {solutions_found} found in {elapsed:.2f}s")
                
                # Check connectivity of first solution
                if solutions_found == 1:
                    check_solution_connectivity(event["solution"]["placements"])
                
                if solutions_found >= 20:
                    break
    
    except Exception as e:
        print(f"Error during solving: {e}")
        import traceback
        traceback.print_exc()
    
    elapsed = time.time() - start_time
    print(f"\nCompleted: {solutions_found} solutions found in {elapsed:.2f} seconds")
    
    if solutions_found >= 20:
        print("SUCCESS: Found 20+ solutions within time limit!")
        return True
    else:
        print(f"PARTIAL: Found {solutions_found} solutions (target was 20)")
        return solutions_found > 0

def check_solution_connectivity(placements):
    """Check if all pieces in solution are connected."""
    print("\nChecking connectivity of first solution:")
    
    # FCC neighbor vectors
    fcc_neighbors = {
        (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
        (1, -1, 0), (-1, 1, 0), (1, 0, -1), (-1, 0, 1), (0, 1, -1), (0, -1, 1)
    }
    
    all_connected = True
    for i, (placement, _) in enumerate(placements):
        piece_name = placement.piece
        cells = placement.covered
        
        if len(cells) == 4:
            # Check if 4 cells form connected component
            pts = [tuple(map(int, c)) for c in cells]
            
            # Build adjacency graph
            adj = {j: [] for j in range(4)}
            for j in range(4):
                for k in range(j + 1, 4):
                    dx = pts[k][0] - pts[j][0]
                    dy = pts[k][1] - pts[j][1]
                    dz = pts[k][2] - pts[j][2]
                    if (dx, dy, dz) in fcc_neighbors or (-dx, -dy, -dz) in fcc_neighbors:
                        adj[j].append(k)
                        adj[k].append(j)
            
            # DFS to check connectivity
            visited = {0}
            stack = [0]
            while stack:
                node = stack.pop()
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        stack.append(neighbor)
            
            is_connected = len(visited) == 4
            status = "connected" if is_connected else "DISCONNECTED"
            print(f"  Piece {i+1} ({piece_name}): {status}")
            
            if not is_connected:
                all_connected = False
                print(f"    Cells: {list(cells)}")
    
    if all_connected:
        print("SUCCESS: All pieces are connected!")
    else:
        print("FAILURE: Some pieces are disconnected!")
    
    return all_connected

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
