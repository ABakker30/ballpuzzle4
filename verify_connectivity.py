#!/usr/bin/env python3
"""Verify connectivity of pieces in solution files."""

import json
import sys
from typing import List, Tuple, Set

# FCC neighbor offsets (engine coordinates - rhombohedral)
FCC_NEIGHBORS = [
    (1,0,0),(0,1,0),(0,0,1), (-1,1,0),(0,-1,1),(1,0,-1),
    (-1,0,0),(0,-1,0),(0,0,-1), (1,-1,0),(0,1,-1),(-1,0,1)
]

def are_adjacent_fcc(cell1: Tuple[int, int, int], cell2: Tuple[int, int, int]) -> bool:
    """Check if two cells are adjacent in FCC lattice."""
    dx = cell2[0] - cell1[0]
    dy = cell2[1] - cell1[1] 
    dz = cell2[2] - cell1[2]
    return (dx, dy, dz) in FCC_NEIGHBORS

def is_piece_connected(cells: List[List[int]]) -> bool:
    """Check if a piece's cells form a connected component in FCC lattice."""
    if len(cells) <= 1:
        return True
    
    # Convert to tuples for easier handling
    cell_tuples = [tuple(cell) for cell in cells]
    cell_set = set(cell_tuples)
    
    # BFS to check connectivity
    visited = {cell_tuples[0]}
    queue = [cell_tuples[0]]
    
    while queue:
        current = queue.pop(0)
        
        # Check all FCC neighbors
        x, y, z = current
        for dx, dy, dz in FCC_NEIGHBORS:
            neighbor = (x + dx, y + dy, z + dz)
            if neighbor in cell_set and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return len(visited) == len(cell_tuples)

def verify_solution_connectivity(solution_file: str):
    """Verify connectivity of all pieces in a solution file."""
    with open(solution_file, 'r') as f:
        data = json.load(f)
    
    print(f"Verifying connectivity in: {solution_file}")
    print(f"Engine: {data.get('solver', {}).get('engine', 'unknown')}")
    print(f"Pieces used: {data.get('piecesUsed', {})}")
    print()
    
    disconnected_pieces = []
    
    for i, placement in enumerate(data.get('placements', [])):
        piece = placement['piece']
        cells = placement['cells_ijk']
        
        is_connected = is_piece_connected(cells)
        status = "CONNECTED" if is_connected else "DISCONNECTED"
        
        print(f"Piece {i+1} ({piece}): {status}")
        print(f"  Cells: {cells}")
        
        if not is_connected:
            disconnected_pieces.append((i+1, piece))
            # Debug: show adjacency matrix for disconnected pieces
            cell_tuples = [tuple(cell) for cell in cells]
            print(f"  Adjacency debug:")
            for j, cell in enumerate(cell_tuples):
                adjacent_cells = []
                for k, other_cell in enumerate(cell_tuples):
                    if cell != other_cell and are_adjacent_fcc(cell, other_cell):
                        adjacent_cells.append(f"{k+1}")
                print(f"    Cell {j+1} {cell} -> adjacent to cells: {', '.join(adjacent_cells) if adjacent_cells else 'none'}")
        print()
    
    if disconnected_pieces:
        print(f"CONNECTIVITY ISSUES FOUND:")
        for piece_num, piece_type in disconnected_pieces:
            print(f"  - Piece {piece_num} ({piece_type}) is disconnected")
    else:
        print("All pieces are properly connected")
    
    return len(disconnected_pieces) == 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_connectivity.py <solution_file.json>")
        sys.exit(1)
    
    solution_file = sys.argv[1]
    is_valid = verify_solution_connectivity(solution_file)
    sys.exit(0 if is_valid else 1)
