#!/usr/bin/env python3
"""Simple debug script to check piece orientations."""

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

# Load sphere orientations data directly
import json
import os

# Load from authoritative source
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y

pieces_lib = load_fcc_A_to_Y()
base_pieces = {}
for name, piece_def in pieces_lib.items():
    if piece_def.orientations:
        # Use first orientation for debugging
        base_pieces[name] = [list(coord) for coord in piece_def.orientations[0]]
    
    print("=== Base piece definitions ===")
    for name, coords in base_pieces.items():
        if name in ['A', 'E', 'T', 'Y']:
            is_connected = is_fcc_connected_4(coords)
            print(f"Piece {name}: {coords} - {'connected' if is_connected else 'DISCONNECTED'}")

# Check some orientations from sphere_orientations.py manually
print("\n=== Sample orientations from sphere_orientations.py ===")

# Sample A orientations
a_orientations = [
    [[0,0,0],[1,0,0],[0,-1,1],[1,-1,1]],
    [[0,0,0],[-1,1,0],[0,0,1],[-1,1,1]],
    [[0,0,0],[0,1,0],[-1,0,1],[-1,1,1]],
]

for i, ori in enumerate(a_orientations):
    is_connected = is_fcc_connected_4(ori)
    print(f"A orientation {i}: {ori} - {'connected' if is_connected else 'DISCONNECTED'}")

# Sample E orientations  
e_orientations = [
    [[0,0,0],[1,0,0],[2,0,0],[1,1,0]],
    [[0,0,0],[1,0,0],[1,1,0],[2,1,0]],
    [[0,0,0],[1,0,0],[0,1,0],[1,0,1]],  # This should be the base E piece
]

print()
for i, ori in enumerate(e_orientations):
    is_connected = is_fcc_connected_4(ori)
    print(f"E orientation {i}: {ori} - {'connected' if is_connected else 'DISCONNECTED'}")
    
    if not is_connected:
        print("  Adjacency details:")
        pts = [tuple(map(int, c)) for c in ori]
        neigh_set = set(FCC_NEIGHBORS)
        for j in range(len(pts)):
            for k in range(j+1, len(pts)):
                dx = pts[k][0] - pts[j][0]
                dy = pts[k][1] - pts[j][1] 
                dz = pts[k][2] - pts[j][2]
                is_adj = (dx, dy, dz) in neigh_set or (-dx, -dy, -dz) in neigh_set
                print(f"    {pts[j]} -> {pts[k]}: delta=({dx},{dy},{dz}) adjacent={is_adj}")
