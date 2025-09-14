#!/usr/bin/env python3
"""Compare DFS and DLX engine solutions to understand connectivity differences."""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# FCC neighbors for connectivity check
FCC_NEIGHBORS = [
    (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
    (1, -1, 0), (-1, 1, 0), (1, 0, -1), (-1, 0, 1), (0, 1, -1), (0, -1, 1)
]

def is_fcc_connected_4(cells):
    """Check if 4 cells form a connected FCC component."""
    if len(cells) != 4:
        return False
    
    pts = [tuple(map(int, c)) for c in cells]
    neigh_set = set(FCC_NEIGHBORS)
    
    # Build adjacency
    adj = {i: [] for i in range(4)}
    for i in range(4):
        xi, yi, zi = pts[i]
        for j in range(i + 1, 4):
            dx = pts[j][0] - xi
            dy = pts[j][1] - yi
            dz = pts[j][2] - zi
            if (dx, dy, dz) in neigh_set or (-dx, -dy, -dz) in neigh_set:
                adj[i].append(j)
                adj[j].append(i)
    
    # DFS from node 0
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    
    return len(seen) == 4

def analyze_solution_file(filepath, engine_name):
    """Analyze a solution file for piece connectivity."""
    print(f"\n=== Analyzing {engine_name} solution: {os.path.basename(filepath)} ===")
    
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
            solution = json.loads(content)
        
        placements = solution.get('placements', [])
        print(f"Number of pieces: {len(placements)}")
        
        disconnected_pieces = []
        
        for i, placement in enumerate(placements):
            piece_name = placement.get('piece', 'Unknown')
            cells = placement.get('cells_ijk', [])
            
            if len(cells) == 4:
                is_connected = is_fcc_connected_4(cells)
                status = "connected" if is_connected else "DISCONNECTED"
                print(f"  Piece {i+1} ({piece_name}): {cells} - {status}")
                
                if not is_connected:
                    disconnected_pieces.append((piece_name, cells))
            else:
                print(f"  Piece {i+1} ({piece_name}): {len(cells)} cells (not 4-cell piece)")
        
        if disconnected_pieces:
            print(f"Found {len(disconnected_pieces)} disconnected pieces:")
            for name, cells in disconnected_pieces:
                print(f"    {name}: {cells}")
        else:
            print("All pieces are connected!")
            
        return len(disconnected_pieces) == 0
        
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None

def find_solution_files():
    """Find solution files from both engines."""
    solution_dirs = [
        "solutions",
        os.path.join("..", "solutions"),
        os.path.join("ballpuzzle", "solutions")
    ]
    
    dfs_files = []
    dlx_files = []
    
    for sol_dir in solution_dirs:
        if os.path.exists(sol_dir):
            for filename in os.listdir(sol_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(sol_dir, filename)
                    if 'dfs' in filename.lower():
                        dfs_files.append(filepath)
                    elif 'dlx' in filename.lower():
                        dlx_files.append(filepath)
    
    return dfs_files, dlx_files

if __name__ == "__main__":
    print("Comparing DFS and DLX engine solutions for connectivity...")
    
    dfs_files, dlx_files = find_solution_files()
    
    print(f"Found {len(dfs_files)} DFS solution files")
    print(f"Found {len(dlx_files)} DLX solution files")
    
    # Analyze a few files from each engine
    dfs_connected = []
    dlx_connected = []
    
    # Analyze existing solution files (these appear to be from DFS engine)
    solution_files = []
    if os.path.exists("solutions"):
        for filename in os.listdir("solutions"):
            if filename.endswith('.json') and not filename.startswith('.'):
                solution_files.append(os.path.join("solutions", filename))
    
    for filepath in solution_files[:3]:  # Check first 3 solution files
        result = analyze_solution_file(filepath, "Current Engine")
        if result is not None:
            dfs_connected.append(result)
    
    print(f"\n=== Summary ===")
    if dfs_connected:
        dfs_all_connected = all(dfs_connected)
        print(f"DFS solutions all connected: {dfs_all_connected}")
    
    if dlx_connected:
        dlx_all_connected = all(dlx_connected)
        print(f"DLX solutions all connected: {dlx_all_connected}")
    
    if not dfs_files and not dlx_files:
        print("No solution files found. Please run the engines first to generate solutions.")
