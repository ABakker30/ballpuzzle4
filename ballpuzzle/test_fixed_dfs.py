#!/usr/bin/env python3
"""Test the fixed DFS engine to verify connected pieces."""

import sys
import os
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

def test_piece_orientations():
    """Test that load_fcc_A_to_Y produces connected orientations."""
    from pieces.library_fcc_v1 import load_fcc_A_to_Y
    
    pieces_dict = load_fcc_A_to_Y()
    
    print("=== Testing load_fcc_A_to_Y orientations ===")
    
    for piece_name in ['A', 'E', 'T', 'Y']:
        if piece_name in pieces_dict:
            pdef = pieces_dict[piece_name]
            print(f"\nPiece {piece_name}:")
            print(f"  Base atoms: {pdef.atoms}")
            print(f"  Total orientations: {len(pdef.orientations)}")
            
            connected_count = 0
            disconnected_count = 0
            
            for i, ori in enumerate(pdef.orientations):
                ori_tuples = [tuple(map(int, c)) for c in ori]
                is_connected = is_fcc_connected_4(ori_tuples)
                
                if is_connected:
                    connected_count += 1
                else:
                    disconnected_count += 1
                    if disconnected_count <= 2:  # Show first few disconnected
                        print(f"    DISCONNECTED orientation {i}: {ori_tuples}")
            
            print(f"  Connected: {connected_count}, Disconnected: {disconnected_count}")
            
            if disconnected_count > 0:
                print(f"  WARNING: Piece {piece_name} has disconnected orientations!")
            else:
                print(f"  ✓ All orientations are connected")

if __name__ == "__main__":
    print("Testing fixed DFS engine piece orientations...")
    test_piece_orientations()
    print("\nTest completed.")
