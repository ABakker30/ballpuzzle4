#!/usr/bin/env python3
"""Simple test for DFS engine with 40 cell container."""

import os
import sys
import json
import subprocess
import time

def run_test():
    """Run DFS engine and check results."""
    
    # Backup existing solutions
    solutions_dir = "solutions"
    if os.path.exists(solutions_dir):
        backup_dir = f"solutions_backup_{int(time.time())}"
        os.rename(solutions_dir, backup_dir)
        print(f"Backed up existing solutions to {backup_dir}")
    
    os.makedirs(solutions_dir, exist_ok=True)
    
    # Run DFS solve
    cmd = [
        sys.executable, 
        "cli/solve.py",
        "data/containers/v1/40 cell.fcc.json",
        "--pieces", "A=1,E=1,T=1,Y=1",
        "--engine", "dfs", 
        "--max-results", "1",
        "--time-limit", "30"
    ]
    
    print("Running DFS engine...")
    result = subprocess.run(cmd, cwd=".", capture_output=True, text=True, timeout=60)
    
    if result.returncode != 0:
        print("DFS solve failed:")
        print("STDERR:", result.stderr)
        return False
    
    print("DFS solve completed successfully!")
    
    # Check solution
    solution_files = [f for f in os.listdir(solutions_dir) if f.endswith('.json')]
    if not solution_files:
        print("No solution files generated")
        return False
    
    latest_file = max(solution_files, key=lambda f: os.path.getmtime(os.path.join(solutions_dir, f)))
    filepath = os.path.join(solutions_dir, latest_file)
    
    print(f"Analyzing solution: {latest_file}")
    
    with open(filepath, 'r') as f:
        solution = json.load(f)
    
    placements = solution.get('placements', [])
    print(f"Solution has {len(placements)} pieces")
    
    # Check connectivity
    fcc_neighbors = [
        (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
        (1, -1, 0), (-1, 1, 0), (1, 0, -1), (-1, 0, 1), (0, 1, -1), (0, -1, 1)
    ]
    neighbor_set = set(fcc_neighbors)
    
    all_connected = True
    for i, placement in enumerate(placements):
        piece_name = placement.get('piece', 'Unknown')
        cells = placement.get('cells_ijk', [])
        
        if len(cells) == 4:
            pts = [tuple(map(int, c)) for c in cells]
            
            # Build adjacency
            adj = {j: [] for j in range(4)}
            for j in range(4):
                for k in range(j + 1, 4):
                    dx = pts[k][0] - pts[j][0]
                    dy = pts[k][1] - pts[j][1]
                    dz = pts[k][2] - pts[j][2]
                    if (dx, dy, dz) in neighbor_set or (-dx, -dy, -dz) in neighbor_set:
                        adj[j].append(k)
                        adj[k].append(j)
            
            # Check connectivity
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
                print(f"    Cells: {cells}")
    
    if all_connected:
        print("SUCCESS: All pieces are connected!")
    else:
        print("FAILURE: Some pieces are disconnected!")
    
    return all_connected

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
