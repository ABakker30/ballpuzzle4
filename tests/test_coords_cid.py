"""Tests for coordinate canonical ID generation."""

import pytest
from src.coords.lattice_fcc import FCCLattice
from src.coords.canonical import CanonicalCoordinate


class TestCanonicalCoordinateID:
    """Test canonical coordinate ID generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lattice = FCCLattice()
        self.canonical = CanonicalCoordinate(self.lattice)
    
    def test_single_coordinate_id(self):
        """Test canonical ID for single coordinate."""
        coords = {(0, 0, 0)}
        cid = self.canonical.get_canonical_id(coords)
        assert cid == "0,0,0"
    
    def test_multiple_coordinates_id(self):
        """Test canonical ID for multiple coordinates."""
        coords = {(0, 0, 0), (1, 0, 0)}
        cid = self.canonical.get_canonical_id(coords)
        # Should be sorted and canonical
        assert "0,0,0" in cid
        assert "1,0,0" in cid
        assert "_" in cid
    
    def test_translated_coordinates_same_id(self):
        """Test that translated coordinates produce same canonical ID."""
        coords1 = {(0, 0, 0), (1, 0, 0)}
        coords2 = {(5, 5, 5), (6, 5, 5)}  # Same shape, translated
        
        cid1 = self.canonical.get_canonical_id(coords1)
        cid2 = self.canonical.get_canonical_id(coords2)
        
        assert cid1 == cid2
    
    def test_rotated_coordinates_same_id(self):
        """Test that rotated coordinates produce same canonical ID."""
        # L-shaped piece in different orientations
        coords1 = {(0, 0, 0), (1, 0, 0), (0, 1, 0)}
        coords2 = {(0, 0, 0), (0, 1, 0), (-1, 0, 0)}  # Rotated 90 degrees
        
        cid1 = self.canonical.get_canonical_id(coords1)
        cid2 = self.canonical.get_canonical_id(coords2)
        
        assert cid1 == cid2
    
    def test_empty_coordinates(self):
        """Test canonical ID for empty coordinate set."""
        coords = set()
        cid = self.canonical.get_canonical_id(coords)
        assert cid == ""
    
    def test_different_shapes_different_ids(self):
        """Test that different shapes produce different canonical IDs."""
        coords1 = {(0, 0, 0), (1, 0, 0)}  # Line
        coords2 = {(0, 0, 0), (0, 1, 0)}  # Different line
        coords3 = {(0, 0, 0), (1, 0, 0), (0, 1, 0)}  # L-shape
        
        cid1 = self.canonical.get_canonical_id(coords1)
        cid2 = self.canonical.get_canonical_id(coords2)
        cid3 = self.canonical.get_canonical_id(coords3)
        
        # All should be the same due to rotational symmetry
        assert cid1 == cid2
        assert cid1 != cid3
    
    def test_canonical_id_deterministic(self):
        """Test that canonical ID generation is deterministic."""
        coords = {(2, 1, 3), (0, 0, 0), (1, 2, 1)}
        
        cid1 = self.canonical.get_canonical_id(coords)
        cid2 = self.canonical.get_canonical_id(coords)
        cid3 = self.canonical.get_canonical_id(coords)
        
        assert cid1 == cid2 == cid3
    
    def test_canonical_transformation(self):
        """Test canonical coordinate transformation."""
        coords = {(5, 3, 7), (6, 3, 7), (5, 4, 7)}
        canonical_coords = self.canonical.to_canonical(coords)
        
        # Should be translated to origin
        assert (0, 0, 0) in canonical_coords
        
        # Should maintain relative positions
        assert len(canonical_coords) == 3
    
    def test_large_coordinate_set(self):
        """Test canonical ID for larger coordinate set."""
        # Create a 2x2x2 cube
        coords = {
            (0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0),
            (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)
        }
        
        cid = self.canonical.get_canonical_id(coords)
        assert cid is not None
        assert len(cid) > 0
        
        # Test that translated version gives same ID
        translated_coords = {(x+10, y+10, z+10) for x, y, z in coords}
        translated_cid = self.canonical.get_canonical_id(translated_coords)
        
        assert cid == translated_cid
