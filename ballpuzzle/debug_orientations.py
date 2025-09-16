#!/usr/bin/env python3
"""Debug orientation differences between DLX and DFS engines."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pieces.library_fcc_v1 import load_fcc_A_to_Y
from pieces.sphere_orientations import get_piece_orientations

def debug_orientation_sources():
    """Compare orientation sources between engines."""
    
    # Load both orientation sources
    pieces_dict = load_fcc_A_to_Y()
    
    print("Debugging orientation sources:")
    print("=" * 50)
    
    for piece_name in ['A', 'E', 'T', 'Y']:
        print(f"\nPiece {piece_name}:")
        
        # DFS source: library_fcc_v1
        piece_def = pieces_dict.get(piece_name)
        if piece_def:
            dfs_orientations = piece_def.orientations
            print(f"  DFS (library_fcc_v1): {len(dfs_orientations)} orientations")
            if dfs_orientations:
                print(f"    First orientation: {dfs_orientations[0]}")
        else:
            print(f"  DFS: No piece definition found")
        
        # DLX source: sphere_orientations
        try:
            dlx_orientations = get_piece_orientations(piece_name)
            print(f"  DLX (sphere_orientations): {len(dlx_orientations)} orientations")
            if dlx_orientations:
                print(f"    First orientation: {dlx_orientations[0]}")
        except Exception as e:
            print(f"  DLX: Error getting orientations: {e}")
        
        # Compare first few orientations if both exist
        if piece_def and piece_def.orientations:
            try:
                dlx_orientations = get_piece_orientations(piece_name)
                dfs_first = piece_def.orientations[0] if piece_def.orientations else None
                dlx_first = dlx_orientations[0] if dlx_orientations else None
                
                if dfs_first and dlx_first:
                    print(f"    Same first orientation: {dfs_first == dlx_first}")
                    if dfs_first != dlx_first:
                        print(f"      DFS: {dfs_first}")
                        print(f"      DLX: {dlx_first}")
            except Exception as e:
                print(f"    Comparison failed: {e}")

if __name__ == "__main__":
    debug_orientation_sources()
