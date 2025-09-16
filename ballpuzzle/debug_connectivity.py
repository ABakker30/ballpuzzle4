#!/usr/bin/env python3
"""Debug connectivity logic on specific piece."""

# FCC neighbor offsets
FCC_NEIGHBORS = [
    (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0),
    (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
    (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1)
]

def are_adjacent_fcc(cell1, cell2):
    """Check if two cells are adjacent in FCC lattice."""
    dx = cell2[0] - cell1[0]
    dy = cell2[1] - cell1[1] 
    dz = cell2[2] - cell1[2]
    return (dx, dy, dz) in FCC_NEIGHBORS

def debug_piece_connectivity(cells):
    """Debug connectivity step by step."""
    print(f"Debugging piece with cells: {cells}")
    
    cell_tuples = [tuple(cell) for cell in cells]
    cell_set = set(cell_tuples)
    
    print(f"Cell set: {cell_set}")
    
    # Show adjacency
    print("Adjacency:")
    for i, cell in enumerate(cell_tuples):
        adjacent = []
        for j, other_cell in enumerate(cell_tuples):
            if cell != other_cell and are_adjacent_fcc(cell, other_cell):
                adjacent.append(j)
        print(f"  Cell {i} {cell} -> adjacent to: {adjacent}")
    
    # BFS step by step
    print("\nBFS connectivity check:")
    visited = {cell_tuples[0]}
    queue = [cell_tuples[0]]
    print(f"Start: visited={visited}, queue={queue}")
    
    step = 0
    while queue:
        step += 1
        current = queue.pop(0)
        print(f"Step {step}: processing {current}")
        
        # Check all FCC neighbors
        x, y, z = current
        for dx, dy, dz in FCC_NEIGHBORS:
            neighbor = (x + dx, y + dy, z + dz)
            if neighbor in cell_set and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                print(f"  Found neighbor {neighbor}, added to queue")
        
        print(f"  After step {step}: visited={visited}, queue={queue}")
    
    is_connected = len(visited) == len(cell_tuples)
    print(f"\nResult: visited {len(visited)}/{len(cell_tuples)} cells -> {'CONNECTED' if is_connected else 'DISCONNECTED'}")
    return is_connected

# Test on Piece 8 (E) which should be connected based on adjacency
piece8_cells = [[-2, 2, 2], [-2, 2, 3], [-2, 3, 2], [-1, 2, 1]]
debug_piece_connectivity(piece8_cells)

print("\n" + "="*50 + "\n")

# Test on Piece 1 (A) which appears disconnected
piece1_cells = [[-5, 2, 5], [-4, 2, 4], [-4, 2, 5], [-3, 2, 4]]
debug_piece_connectivity(piece1_cells)
