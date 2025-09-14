#!/usr/bin/env python3
"""
Debug which pieces are available in sphere_orientations.
"""

from src.pieces.sphere_orientations import get_piece_orientations

def test_all_pieces():
    """Test which pieces are available in sphere_orientations."""
    all_pieces = 'ABCDEFGHIJKLMNOPQRSTUVWXY'
    
    available = []
    missing = []
    
    for piece in all_pieces:
        try:
            orientations = get_piece_orientations(piece)
            available.append(piece)
            print(f"{piece}: {len(orientations)} orientations")
        except KeyError:
            missing.append(piece)
    
    print(f"\nAvailable pieces ({len(available)}): {available}")
    print(f"Missing pieces ({len(missing)}): {missing}")

if __name__ == "__main__":
    test_all_pieces()
