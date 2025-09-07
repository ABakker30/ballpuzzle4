"""FCC piece library version 1 - standard ball puzzle pieces."""

from typing import Dict, List, Set, Tuple
import numpy as np
from ..coords.lattice_fcc import FCCLattice
from ..coords.canonical import CanonicalCoordinate


class FCCPieceLibraryV1:
    """Standard library of FCC ball puzzle pieces.
    
    Contains definitions for common ball puzzle pieces
    in face-centered cubic coordinates.
    """
    
    def __init__(self):
        """Initialize the piece library."""
        self.lattice = FCCLattice()
        self.canonical = CanonicalCoordinate(self.lattice)
        self._pieces = self._define_pieces()
    
    def _define_pieces(self) -> Dict[str, Set[Tuple[int, int, int]]]:
        """Define all standard pieces in the library.
        
        Returns:
            Dictionary mapping piece names to coordinate sets
        """
        pieces = {}
        
        # Single ball
        pieces["single"] = {(0, 0, 0)}
        
        # Linear pieces
        pieces["line2"] = {(0, 0, 0), (1, 0, 0)}
        pieces["line3"] = {(0, 0, 0), (1, 0, 0), (2, 0, 0)}
        pieces["line4"] = {(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)}
        
        # L-shaped pieces
        pieces["L3"] = {(0, 0, 0), (1, 0, 0), (0, 1, 0)}
        pieces["L4"] = {(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0)}
        pieces["L5"] = {(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (0, 1, 0)}
        
        # T-shaped pieces
        pieces["T4"] = {(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 1, 0)}
        pieces["T5"] = {(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (1, 1, 0)}
        
        # Square and rectangular pieces
        pieces["square4"] = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)}
        pieces["rect6"] = {(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (1, 1, 0), (2, 1, 0)}
        
        # Z-shaped pieces
        pieces["Z4"] = {(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0)}
        pieces["Z5"] = {(0, 0, 0), (1, 0, 0), (1, 1, 0), (2, 1, 0), (2, 2, 0)}
        
        # 3D pieces
        pieces["corner3d"] = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)}
        pieces["tetrahedron"] = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)}
        
        # Complex 3D pieces
        pieces["pyramid5"] = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1)}
        pieces["cross3d"] = {(0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)}
        
        # Canonicalize all pieces
        canonical_pieces = {}
        for name, coords in pieces.items():
            canonical_pieces[name] = self.canonical.to_canonical(coords)
        
        return canonical_pieces
    
    def get_piece(self, name: str) -> Set[Tuple[int, int, int]]:
        """Get piece coordinates by name.
        
        Args:
            name: Piece name
            
        Returns:
            Set of FCC coordinates for the piece
            
        Raises:
            KeyError: If piece name not found
        """
        if name not in self._pieces:
            raise KeyError(f"Piece '{name}' not found in library")
        return self._pieces[name].copy()
    
    def get_all_pieces(self) -> Dict[str, Set[Tuple[int, int, int]]]:
        """Get all pieces in the library.
        
        Returns:
            Dictionary of all pieces
        """
        return {name: coords.copy() for name, coords in self._pieces.items()}
    
    def get_piece_names(self) -> List[str]:
        """Get list of all piece names.
        
        Returns:
            List of piece names
        """
        return list(self._pieces.keys())
    
    def get_piece_size(self, name: str) -> int:
        """Get the number of balls in a piece.
        
        Args:
            name: Piece name
            
        Returns:
            Number of balls in the piece
        """
        return len(self.get_piece(name))
    
    def get_pieces_by_size(self, size: int) -> List[str]:
        """Get all pieces with a specific number of balls.
        
        Args:
            size: Number of balls
            
        Returns:
            List of piece names with the specified size
        """
        return [name for name, coords in self._pieces.items() if len(coords) == size]
    
    def generate_orientations(self, piece_name: str) -> List[Set[Tuple[int, int, int]]]:
        """Generate all unique orientations of a piece.
        
        Args:
            piece_name: Name of the piece
            
        Returns:
            List of unique orientations (canonical forms)
        """
        base_piece = self.get_piece(piece_name)
        orientations = set()
        
        # Apply all 24 rotations
        rotation_matrices = self.canonical._generate_rotation_matrices()
        
        for rotation in rotation_matrices:
            rotated_coords = set()
            for coord in base_piece:
                coord_array = np.array(coord)
                rotated = rotation @ coord_array
                rotated_int = tuple(np.round(rotated).astype(int))
                rotated_coords.add(rotated_int)
            
            # Canonicalize the rotated piece
            canonical_rotated = self.canonical.to_canonical(rotated_coords)
            orientations.add(frozenset(canonical_rotated))
        
        return [set(orientation) for orientation in orientations]
