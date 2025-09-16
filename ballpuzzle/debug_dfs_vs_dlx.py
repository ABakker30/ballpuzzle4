#!/usr/bin/env python3
"""
Debug DFS vs DLX orientation handling to see why DFS doesn't find solutions.
"""

from src.pieces.sphere_orientations import get_piece_orientations
from src.solver.engines.engine_c.lattice_fcc import validate_fcc_connectivity
from src.io.container import load_container
import json

def debug_orientations():
    """Debug orientation handling for both engines."""
    
    # Load a simple container
    container = load_container("data/containers/v1/16 cell container.fcc.json")
    container_cells = set(tuple(cell) for cell in container['cells'])
    
    print(f"Container has {len(container_cells)} cells")
    print(f"First few cells: {list(container_cells)[:5]}")
    
    # Test each piece type
    for piece_name in ['A', 'E', 'T', 'Y']:
        print(f"\n=== {piece_name} piece ===")
        
        try:
            orientations = get_piece_orientations(piece_name)
            print(f"Total orientations: {len(orientations)}")
            
            valid_placements = 0
            for ori_idx, ori in enumerate(orientations):
                if not ori:
                    continue
                    
                # Convert to tuples
                ori_cells = [tuple(cell) for cell in ori]
                
                # Check connectivity
                connected = validate_fcc_connectivity(ori_cells)
                if not connected:
                    continue
                
                # Try placing at first container cell
                first_container_cell = next(iter(container_cells))
                first_piece_cell = ori_cells[0]
                
                # Calculate translation
                t = (first_container_cell[0] - first_piece_cell[0], 
                     first_container_cell[1] - first_piece_cell[1], 
                     first_container_cell[2] - first_piece_cell[2])
                
                # Calculate covered cells
                covered = tuple((t[0] + cell[0], t[1] + cell[1], t[2] + cell[2]) for cell in ori_cells)
                
                # Check if all covered cells are in container
                if all(cell in container_cells for cell in covered):
                    valid_placements += 1
                    if valid_placements <= 3:  # Show first 3 valid placements
                        print(f"  Valid placement {valid_placements}: ori {ori_idx}, t={t}, covered={covered}")
            
            print(f"Valid placements for {piece_name}: {valid_placements}")
            
        except KeyError:
            print(f"KeyError - piece {piece_name} not found in sphere_orientations")

if __name__ == "__main__":
    debug_orientations()
