"""Tests for symmetry breaking with small puzzle instances."""

import pytest
from src.coords.symmetry_fcc import ROTATIONS_24, canonical_atom_tuple
from src.solver.symbreak import container_symmetry_group, anchor_rule_filter
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y


class TestSymmetrySmall:
    """Test symmetry breaking on small puzzle instances."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.piece_lib = load_fcc_A_to_Y()
    
    def test_container_symmetry_group(self):
        """Test container symmetry group calculation."""
        # Use FCC-symmetric 7-cell cross (origin + 6 neighbors)
        container = [(0,0,0),(1,0,0),(0,1,0),(0,0,1),(-1,1,0),(0,-1,1),(1,0,-1)]
        sym_group = container_symmetry_group(container)
        
        # Should have multiple symmetries for this FCC-symmetric shape
        assert len(sym_group) > 1
        assert len(sym_group) <= 24  # Max possible FCC rotations
    
    def test_anchor_rule_basic(self):
        """Test basic anchor rule filtering."""
        # Create some test placements
        placements = [
            ("A", ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0))),
            ("A", ((0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0))),  # Duplicate
        ]
        
        min_cell = (0, 0, 0)
        sym_group = ROTATIONS_24
        
        filtered = anchor_rule_filter(placements, min_cell, "A", sym_group)
        
        # Should filter out duplicates
        assert len(filtered) <= len(placements)
        
        # All filtered placements should cover min_cell
        for piece, atoms in filtered:
            assert min_cell in atoms
