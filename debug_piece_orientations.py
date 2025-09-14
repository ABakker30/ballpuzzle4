#!/usr/bin/env python3
"""
Debug piece orientations to verify connectivity and compare with solution data.
"""

import json
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
from analyze_connectivity import is_connected, get_fcc_neighbors

def debug_piece_orientations():
    """Debug T piece orientations and check connectivity."""
    pieces = load_fcc_A_to_Y()
    t_piece = pieces['T']
    
    print(f"T piece base atoms: {t_piece.atoms}")
    print(f"Total orientations: {len(t_piece.orientations)}")
    print()
    
    # Check connectivity of all orientations
    disconnected_orientations = []
    
    for i, orientation in enumerate(t_piece.orientations):
        connected = is_connected(list(orientation))
        print(f"Orientation {i}: {orientation} - {'Connected' if connected else 'DISCONNECTED'}")
        
        if not connected:
            disconnected_orientations.append((i, orientation))
    
    if disconnected_orientations:
        print(f"\nFound {len(disconnected_orientations)} disconnected orientations!")
        for ori_idx, orientation in disconnected_orientations:
            print(f"  Orientation {ori_idx}: {orientation}")
    else:
        print("\nAll orientations are properly connected.")
    
    # Now check the specific problematic orientations from solutions
    print("\n" + "="*60)
    print("CHECKING PROBLEMATIC ORIENTATIONS FROM SOLUTIONS:")
    
    problematic_cells = [
        [(-3, 3, 5), (-3, 5, 3), (-2, 2, 5), (-2, 3, 4)],  # T ori 21
        [(-2, 2, 4), (-2, 4, 2), (-2, 4, 3), (-2, 5, 2)],  # T ori 2
        [(-1, 2, 3), (-1, 4, 1), (-1, 4, 2), (-1, 5, 1)]   # T ori 2
    ]
    
    for i, cells in enumerate(problematic_cells):
        print(f"\nProblematic set {i+1}: {cells}")
        connected = is_connected(cells)
        print(f"Connected: {connected}")
        
        if not connected:
            # Try to find which cells are connected to which
            cell_set = set(cells)
            components = []
            visited = set()
            
            for cell in cells:
                if cell in visited:
                    continue
                
                # BFS to find connected component
                component = []
                queue = [cell]
                
                while queue:
                    current = queue.pop(0)
                    if current in visited:
                        continue
                    visited.add(current)
                    component.append(current)
                    
                    for neighbor in get_fcc_neighbors(current):
                        if neighbor in cell_set and neighbor not in visited:
                            queue.append(neighbor)
                
                components.append(component)
            
            print(f"  Found {len(components)} disconnected components:")
            for j, comp in enumerate(components):
                print(f"    Component {j+1}: {comp}")

if __name__ == "__main__":
    debug_piece_orientations()
