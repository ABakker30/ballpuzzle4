#!/usr/bin/env python3
"""Simple test script for the fixed DFS engine."""

import sys
import os
import json
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_dfs_engine():
    """Test the DFS engine with a simple container and inventory."""
    try:
        from solver.engines.dfs_engine import DFSEngine
        
        # Simple test container (8 cells)
        container = [
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
            [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]
        ]
        
        # Simple inventory (2 pieces of 4 cells each)
        inventory = {"A": 1, "E": 1}
        
        # Engine options
        options = {
            "max_results": 1,
            "time_limit": 10,
            "seed": 42
        }
        
        print("Testing DFS engine with 8-cell container and A=1, E=1...")
        
        engine = DFSEngine()
        events = list(engine.solve(container, inventory, options))
        
        solutions = [event for event in events if event.get("type") == "solution"]
        
        if solutions:
            solution = solutions[0]["solution"]
            placements = solution["placements"]
            
            print(f"Found solution with {len(placements)} pieces:")
            
            # Check connectivity of each piece
            all_connected = True
            for i, (placement, _) in enumerate(placements):
                piece_name = placement.piece
                cells = placement.covered
                
                # Check if 4 cells are connected in FCC lattice
                is_connected = check_connectivity(cells)
                status = "connected" if is_connected else "DISCONNECTED"
                
                print(f"  Piece {i+1} ({piece_name}): {list(cells)} - {status}")
                
                if not is_connected:
                    all_connected = False
            
            if all_connected:
                print("✓ SUCCESS: All pieces are connected!")
                return True
            else:
                print("✗ FAILURE: Some pieces are disconnected!")
                return False
        else:
            print("No solutions found")
            return False
            
    except Exception as e:
        print(f"Error testing DFS engine: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_connectivity(cells):
    """Check if cells form a connected component in FCC lattice."""
    if len(cells) != 4:
        return False
    
    # FCC neighbors
    neighbors = [
        (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
        (1, -1, 0), (-1, 1, 0), (1, 0, -1), (-1, 0, 1), (0, 1, -1), (0, -1, 1)
    ]
    neighbor_set = set(neighbors)
    
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
    
    # DFS to check connectivity
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
    success = test_dfs_engine()
    if success:
        print("\n🎉 DFS engine test PASSED - all pieces are connected!")
    else:
        print("\n❌ DFS engine test FAILED - disconnected pieces found!")
    sys.exit(0 if success else 1)
