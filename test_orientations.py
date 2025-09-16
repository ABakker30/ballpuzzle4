#!/usr/bin/env python3
"""Test DFS engine with get_piece_orientations to debug failure."""

import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pieces.library_fcc_v1 import load_fcc_A_to_Y
from pieces.sphere_orientations import get_piece_orientations

def test_orientation_access():
    """Test accessing orientations from both sources."""
    
    print("Testing orientation access:")
    print("=" * 40)
    
    # Test library_fcc_v1 (current DFS method)
    try:
        pieces_dict = load_fcc_A_to_Y()
        piece_A = pieces_dict.get('A')
        if piece_A and hasattr(piece_A, 'orientations'):
            print(f"✅ DFS method: A has {len(piece_A.orientations)} orientations")
            print(f"   First orientation type: {type(piece_A.orientations[0])}")
            print(f"   First orientation: {piece_A.orientations[0]}")
        else:
            print("❌ DFS method: Failed to get A orientations")
    except Exception as e:
        print(f"❌ DFS method error: {e}")
    
    # Test sphere_orientations (DLX method)
    try:
        orientations_A = get_piece_orientations('A')
        print(f"✅ DLX method: A has {len(orientations_A)} orientations")
        print(f"   First orientation type: {type(orientations_A[0])}")
        print(f"   First orientation: {orientations_A[0]}")
    except Exception as e:
        print(f"❌ DLX method error: {e}")
    
    # Test compatibility
    try:
        pieces_dict = load_fcc_A_to_Y()
        piece_A = pieces_dict.get('A')
        orientations_A = get_piece_orientations('A')
        
        if piece_A and piece_A.orientations and orientations_A:
            dfs_count = len(piece_A.orientations)
            dlx_count = len(orientations_A)
            print(f"\nOrientation counts - DFS: {dfs_count}, DLX: {dlx_count}")
            
            # Check if they're the same data
            if dfs_count > 0 and dlx_count > 0:
                dfs_first = piece_A.orientations[0]
                dlx_first = orientations_A[0]
                print(f"First orientations match: {dfs_first == dlx_first}")
                
    except Exception as e:
        print(f"❌ Compatibility test error: {e}")

def simulate_dfs_with_dlx_orientations():
    """Simulate DFS engine using DLX orientation method."""
    
    print("\nSimulating DFS with DLX orientations:")
    print("=" * 40)
    
    try:
        # Test piece enumeration like DFS engine does
        pieces_dict = load_fcc_A_to_Y()
        piece_order = ['A', 'E', 'T', 'Y']
        
        for piece in piece_order:
            piece_def = pieces_dict.get(piece)
            if piece_def is None:
                print(f"❌ {piece}: No piece definition")
                continue
            
            # Try DLX method
            try:
                orientations = get_piece_orientations(piece)
                print(f"✅ {piece}: {len(orientations)} orientations via DLX method")
                
                # Test enumeration like DFS does
                orientations_enum = list(enumerate(orientations))
                print(f"   Enumerated: {len(orientations_enum)} items")
                
                # Test accessing first orientation
                if orientations_enum:
                    ori_idx, ori = orientations_enum[0]
                    if ori:
                        first_cell = ori[0]
                        print(f"   First cell of first orientation: {first_cell}")
                    else:
                        print(f"   First orientation is empty/None")
                        
            except KeyError:
                print(f"❌ {piece}: KeyError from get_piece_orientations")
            except Exception as e:
                print(f"❌ {piece}: Error - {e}")
                
    except Exception as e:
        print(f"❌ Simulation failed: {e}")

if __name__ == "__main__":
    test_orientation_access()
    simulate_dfs_with_dlx_orientations()
