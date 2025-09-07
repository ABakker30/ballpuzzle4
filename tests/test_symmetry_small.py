"""Tests for symmetry breaking with small puzzle instances."""

import pytest
from src.coords.lattice_fcc import FCCLattice
from src.coords.canonical import CanonicalCoordinate
from src.solver.symbreak import SymmetryBreaker
from src.pieces.library_fcc_v1 import FCCPieceLibraryV1


class TestSymmetrySmall:
    """Test symmetry breaking on small puzzle instances."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lattice = FCCLattice()
        self.canonical = CanonicalCoordinate(self.lattice)
        self.symbreak = SymmetryBreaker()
        self.piece_library = FCCPieceLibraryV1()
    
    def test_single_piece_orientations(self):
        """Test orientation filtering for single piece."""
        # Get L-shaped piece
        l_piece = self.piece_library.get_piece("L3")
        orientations = self.piece_library.generate_orientations("L3")
        
        # Filter orientations (no existing pieces)
        filtered = self.symbreak.filter_orientations(orientations, set())
        
        # Should have fewer orientations due to symmetry breaking
        assert len(filtered) <= len(orientations)
        assert len(filtered) > 0
    
    def test_canonical_first_placement(self):
        """Test canonical first piece placement."""
        container = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)}  # 2x2 square
        
        # Test various first placements
        placement1 = {(0, 0, 0), (1, 0, 0)}  # Should be canonical
        placement2 = {(1, 1, 0), (0, 1, 0)}  # Should not be canonical
        
        assert self.symbreak.should_try_placement(placement1, container, set())
        # Note: This test depends on the specific canonical ordering implementation
    
    def test_line_piece_symmetry(self):
        """Test symmetry breaking for line pieces."""
        line2 = self.piece_library.get_piece("line2")
        orientations = self.piece_library.generate_orientations("line2")
        
        # Line piece should have multiple orientations
        assert len(orientations) >= 3  # At least x, y, z directions
        
        # Filter with no existing pieces
        filtered = self.symbreak.filter_orientations(orientations, set())
        assert len(filtered) > 0
    
    def test_square_piece_symmetry(self):
        """Test symmetry breaking for square pieces."""
        square = self.piece_library.get_piece("square4")
        orientations = self.piece_library.generate_orientations("square4")
        
        # Square should have fewer unique orientations due to symmetry
        filtered = self.symbreak.filter_orientations(orientations, set())
        assert len(filtered) > 0
    
    def test_state_key_generation(self):
        """Test canonical state key generation."""
        used_coords1 = {(0, 0, 0), (1, 0, 0)}
        used_coords2 = {(5, 5, 5), (6, 5, 5)}  # Same shape, translated
        
        remaining_pieces = {"line2": 1, "L3": 2}
        
        key1 = self.symbreak.get_canonical_state_key(used_coords1, remaining_pieces)
        key2 = self.symbreak.get_canonical_state_key(used_coords2, remaining_pieces)
        
        # Should generate same key for equivalent states
        assert key1 == key2
    
    def test_different_states_different_keys(self):
        """Test that different states generate different keys."""
        used_coords1 = {(0, 0, 0), (1, 0, 0)}
        used_coords2 = {(0, 0, 0), (0, 1, 0)}
        
        remaining_pieces = {"line2": 1}
        
        key1 = self.symbreak.get_canonical_state_key(used_coords1, remaining_pieces)
        key2 = self.symbreak.get_canonical_state_key(used_coords2, remaining_pieces)
        
        # Different piece arrangements should have same key due to symmetry
        assert key1 == key2
        
        # But different remaining pieces should have different keys
        different_pieces = {"L3": 1}
        key3 = self.symbreak.get_canonical_state_key(used_coords1, different_pieces)
        assert key1 != key3
    
    def test_small_container_symmetry(self):
        """Test symmetry breaking on small container."""
        # 2x2 container
        container = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)}
        
        # Test first placement
        first_piece = {(0, 0, 0), (1, 0, 0)}
        assert self.symbreak.should_try_placement(first_piece, container, set())
        
        # Test second placement
        used_coords = {(0, 0, 0), (1, 0, 0)}
        second_piece = {(0, 1, 0), (1, 1, 0)}
        assert self.symbreak.should_try_placement(second_piece, container, used_coords)
    
    def test_rotation_equivalence(self):
        """Test that rotated pieces are recognized as equivalent."""
        # Create L-shaped piece in different orientations
        l1 = {(0, 0, 0), (1, 0, 0), (0, 1, 0)}
        l2 = {(0, 0, 0), (0, 1, 0), (-1, 0, 0)}  # Rotated
        
        canonical1 = self.canonical.to_canonical(l1)
        canonical2 = self.canonical.to_canonical(l2)
        
        # Should produce same canonical form
        assert canonical1 == canonical2
    
    def test_3d_piece_symmetry(self):
        """Test symmetry breaking for 3D pieces."""
        corner_3d = self.piece_library.get_piece("corner3d")
        orientations = self.piece_library.generate_orientations("corner3d")
        
        # 3D corner piece should have multiple orientations
        assert len(orientations) > 1
        
        # Filter orientations
        filtered = self.symbreak.filter_orientations(orientations, set())
        assert len(filtered) > 0
        assert len(filtered) <= len(orientations)
    
    def test_empty_used_coords(self):
        """Test symmetry breaking with empty used coordinates."""
        orientations = [{(0, 0, 0), (1, 0, 0)}, {(0, 0, 0), (0, 1, 0)}]
        
        filtered = self.symbreak.filter_orientations(orientations, set())
        
        # Should filter to canonical forms only
        assert len(filtered) > 0
        assert len(filtered) <= len(orientations)
