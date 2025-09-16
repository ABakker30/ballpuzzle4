#!/usr/bin/env python3
"""
Static piece orientations from legacy system - no dynamic generation.
"""

from typing import Dict, List, Tuple

# Legacy piece orientations - exactly as provided by the working system
LEGACY_PIECE_ORIENTATIONS = {
    "A": [
        [[0, 0, 0], [1, 0, 0], [0, -1, 1], [1, -1, 1]],
        [[0, 0, 0], [-1, 1, 0], [0, 0, 1], [-1, 1, 1]],
        [[0, 0, 0], [0, 1, 0], [-1, 0, 1], [-1, 1, 1]]
    ],
    "B": [
        [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [[0, 0, 0], [0, 1, 0], [-1, 0, 1], [0, 0, 1]],
        [[0, 0, 0], [-1, 1, 0], [0, 1, 0], [0, 0, 1]],
        [[0, 0, 0], [1, 0, 0], [1, -1, 1], [0, 0, 1]],
        [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 1]],
        [[0, 0, 0], [0, 1, 0], [-1, 0, 1], [0, 1, 1]],
        [[0, 0, 0], [-1, 1, 0], [0, 1, 0], [-1, 1, 1]],
        [[0, 0, 0], [1, 0, 0], [1, -1, 1], [1, 0, 1]]
    ],
    # Add remaining pieces with their exact legacy orientations...
    # For now, using counts from analysis - full data would be loaded from legacy system
}

def get_piece_orientations(piece_name: str) -> List[List[List[int]]]:
    """Get all orientations for a piece.
    
    Args:
        piece_name: Name of the piece (A-Y)
        
    Returns:
        List of orientations, each orientation is a list of [x,y,z] coordinates
        
    Raises:
        KeyError: If piece not found
    """
    if piece_name not in LEGACY_PIECE_ORIENTATIONS:
        raise KeyError(f"Piece '{piece_name}' not found in legacy orientations")
    
    return LEGACY_PIECE_ORIENTATIONS[piece_name]

def get_piece_orientation_count(piece_name: str) -> int:
    """Get the number of orientations for a piece.
    
    Args:
        piece_name: Name of the piece
        
    Returns:
        Number of orientations
    """
    return len(get_piece_orientations(piece_name))

def get_all_piece_names() -> List[str]:
    """Get all available piece names.
    
    Returns:
        List of piece names
    """
    return list(LEGACY_PIECE_ORIENTATIONS.keys())
