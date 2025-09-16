#!/usr/bin/env python3
"""Debug script to trace disconnected pieces in DFS engine."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pieces.sphere_orientations import get_piece_orientations
from solver.engines.dfs_engine import _is_fcc_connected_4

def debug_piece_orientations():
    """Check connectivity of orientations for key pieces."""
    pieces_to_check = ['A', 'E', 'T', 'Y']
    
    for piece_name in pieces_to_check:
        print(f"\n=== Piece {piece_name} ===")
        try:
            orientations = get_piece_orientations(piece_name)
            print(f"Total orientations: {len(orientations)}")
            
            connected_count = 0
            disconnected_count = 0
            disconnected_examples = []
            
            for i, ori in enumerate(orientations):
                # Convert to tuples for connectivity check
                ori_tuples = [tuple(map(int, c)) for c in ori]
                is_connected = _is_fcc_connected_4(ori_tuples)
                
                if is_connected:
                    connected_count += 1
                else:
                    disconnected_count += 1
                    if len(disconnected_examples) < 3:
                        disconnected_examples.append((i, ori_tuples))
            
            print(f"Connected: {connected_count}")
            print(f"Disconnected: {disconnected_count}")
            
            if disconnected_examples:
                print("Disconnected examples:")
                for idx, ori in disconnected_examples:
                    print(f"  Orientation {idx}: {ori}")
                    
        except Exception as e:
            print(f"Error processing piece {piece_name}: {e}")

def debug_specific_orientation():
    """Debug a specific orientation to understand connectivity."""
    # Test piece E orientation that might be disconnected
    piece_name = 'E'
    orientations = get_piece_orientations(piece_name)
    
    print(f"\n=== Detailed connectivity check for piece {piece_name} ===")
    
    for i, ori in enumerate(orientations[:5]):  # Check first 5 orientations
        ori_tuples = [tuple(map(int, c)) for c in ori]
        is_connected = _is_fcc_connected_4(ori_tuples)
        
        print(f"\nOrientation {i}: {ori_tuples}")
        print(f"Connected: {is_connected}")
        
        if not is_connected:
            # Manual connectivity check
            print("Manual adjacency check:")
            from solver.engines.engine_c.lattice_fcc import FCC_NEIGHBORS
            neigh_set = set(FCC_NEIGHBORS)
            
            for j, cell1 in enumerate(ori_tuples):
                for k, cell2 in enumerate(ori_tuples):
                    if j < k:
                        dx = cell2[0] - cell1[0]
                        dy = cell2[1] - cell1[1] 
                        dz = cell2[2] - cell1[2]
                        is_adjacent = (dx, dy, dz) in neigh_set or (-dx, -dy, -dz) in neigh_set
                        print(f"  {cell1} -> {cell2}: delta=({dx},{dy},{dz}) adjacent={is_adjacent}")

if __name__ == "__main__":
    print("Debugging disconnected pieces in DFS engine...")
    debug_piece_orientations()
    debug_specific_orientation()
