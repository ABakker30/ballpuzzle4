#!/usr/bin/env python3
"""Test DFS engine with 40 cell container and analyze connectivity."""

import os
import sys
import json
import subprocess
import time

def run_dfs_test():
    """Run DFS engine test with 40 cell container."""
    
    # First, backup existing solutions
    solutions_dir = "solutions"
    if os.path.exists(solutions_dir):
        backup_dir = f"solutions_backup_{int(time.time())}"
        os.rename(solutions_dir, backup_dir)
        print(f"Backed up existing solutions to {backup_dir}")
    
    # Create new solutions directory
    os.makedirs(solutions_dir, exist_ok=True)
    
    # Run the DFS engine using the existing CLI
    try:
        # Try to run the solve command
        cmd = [
            sys.executable, 
            "cli/solve.py",
            "data/containers/v1/40 cell.fcc.json",
            "--pieces", "A=1,E=1,T=1,Y=1",
            "--engine", "dfs", 
            "--max-results", "1",
            "--time-limit", "30"
        ]
        
        print("Running DFS engine test...")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=".", capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ DFS solve completed successfully!")
            if result.stdout:
                print("Output preview:", result.stdout[:200])
        else:
            print(f"✗ DFS solve failed with return code {result.returncode}")
            if result.stderr:
                print("Error:", result.stderr[:500])
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ DFS solve timed out")
        return False
    except Exception as e:
        print(f"✗ Error running DFS solve: {e}")
        return False
    
    # Analyze the generated solution
    return analyze_solution()

def analyze_solution():
    """Analyze the most recent solution for connectivity."""
    solutions_dir = "solutions"
    
    if not os.path.exists(solutions_dir):
        print("No solutions directory found")
        return False
    
    solution_files = [f for f in os.listdir(solutions_dir) if f.endswith('.json')]
    if not solution_files:
        print("No solution files found")
        return False
    
    # Get the most recent solution file
    latest_file = max(solution_files, key=lambda f: os.path.getmtime(os.path.join(solutions_dir, f)))
    filepath = os.path.join(solutions_dir, latest_file)
    
    print(f"\nAnalyzing solution: {latest_file}")
    
    try:
        with open(filepath, 'r') as f:
            solution = json.load(f)
        
        placements = solution.get('placements', [])
        print(f"Solution contains {len(placements)} pieces")
        
        all_connected = True
        disconnected_pieces = []
        
        for i, placement in enumerate(placements):
            piece_name = placement.get('piece', 'Unknown')
            cells = placement.get('cells_ijk', [])
            
            if len(cells) == 4:
                is_connected = check_fcc_connectivity(cells)
                status = "connected" if is_connected else "DISCONNECTED"
                print(f"  Piece {i+1} ({piece_name}): {status}")
                
                if not is_connected:
                    all_connected = False
                    disconnected_pieces.append((piece_name, cells))
        
        if all_connected:
            print("\n🎉 SUCCESS: All pieces are connected!")
            print("The DFS engine fix is working correctly.")
        else:
            print(f"\n❌ FAILURE: Found {len(disconnected_pieces)} disconnected pieces:")
            for name, cells in disconnected_pieces:
                print(f"    {name}: {cells}")
        
        return all_connected
        
    except Exception as e:
        print(f"Error analyzing solution: {e}")
        return False

def check_fcc_connectivity(cells):
    """Check if 4 cells form a connected component in FCC lattice."""
    if len(cells) != 4:
        return False
    
    # FCC neighbor vectors
    fcc_neighbors = [
        (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
        (1, -1, 0), (-1, 1, 0), (1, 0, -1), (-1, 0, 1), (0, 1, -1), (0, -1, 1)
    ]
    neighbor_set = set(fcc_neighbors)
    
    pts = [tuple(map(int, c)) for c in cells]
    
    # Build adjacency graph
    adj = {i: [] for i in range(4)}
    for i in range(4):
        for j in range(i + 1, 4):
            dx = pts[j][0] - pts[i][0]
            dy = pts[j][1] - pts[i][1]
            dz = pts[j][2] - pts[i][2]
            if (dx, dy, dz) in neighbor_set or (-dx, -dy, -dz) in neighbor_set:
                adj[i].append(j)
                adj[j].append(i)
    
    # DFS to check if all 4 cells are connected
    visited = {0}
    stack = [0]
    while stack:
        node = stack.pop()
        for neighbor in adj[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)
    
    return len(visited) == 4

if __name__ == "__main__":
    print("Testing fixed DFS engine with 40 cell container...")
    success = run_dfs_test()
    
    if success:
        print("\n✅ TEST PASSED: DFS engine produces connected pieces!")
    else:
        print("\n❌ TEST FAILED: DFS engine still has disconnected pieces!")
    
    sys.exit(0 if success else 1)
