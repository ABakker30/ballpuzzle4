#!/usr/bin/env python3
"""
Debug orientation formats between piece library and sphere_orientations.
"""

from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
from src.pieces.sphere_orientations import get_piece_orientations

def debug_orientation_formats():
    """Compare orientation formats between the two sources."""
    pieces_dict = load_fcc_A_to_Y()
    
    # Test with A piece
    piece_name = "A"
    
    print(f"=== {piece_name} PIECE ORIENTATIONS ===")
    
    # From piece library
    piece_def = pieces_dict[piece_name]
    library_orientations = piece_def.orientations
    
    # From sphere_orientations
    sphere_orientations = get_piece_orientations(piece_name)
    
    print(f"Library orientations count: {len(library_orientations)}")
    print(f"Sphere orientations count: {len(sphere_orientations)}")
    
    print(f"\nFirst 3 library orientations:")
    for i, ori in enumerate(library_orientations[:3]):
        print(f"  {i}: {ori}")
    
    print(f"\nFirst 3 sphere orientations:")
    for i, ori in enumerate(sphere_orientations[:3]):
        print(f"  {i}: {ori}")
    
    print(f"\nData types:")
    if library_orientations:
        print(f"  Library: {type(library_orientations[0])}, element: {type(library_orientations[0][0])}")
    if sphere_orientations:
        print(f"  Sphere: {type(sphere_orientations[0])}, element: {type(sphere_orientations[0][0])}")

if __name__ == "__main__":
    debug_orientation_formats()
