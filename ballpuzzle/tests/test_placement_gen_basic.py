"""Basic unit test for placement generator."""

import pytest
from src.solver.placement_gen import for_target, Placement
from src.solver.tt import OccMask
from src.pieces.library_fcc_v1 import PieceDef

def test_basic_for_target_in_bounds():
    """Test that placements stay within container and respect occupancy."""
    
    # Create a tiny container
    container = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)}
    cells_sorted = sorted(container)
    occ = OccMask(cells_sorted)
    
    # Create a tiny test piece: two atoms in neighbor relation
    tiny_piece = PieceDef("Z", [(0, 0, 0), (1, 0, 0)])
    lib = {"Z": tiny_piece}
    
    # Mock piece bag
    class MockBag:
        def __init__(self):
            self.pieces = {"Z": 1}
        
        def to_dict(self):
            return dict(self.pieces)
    
    bag = MockBag()
    
    # Generate placements for target (0,0,0)
    cands = for_target((0, 0, 0), occ, bag, lib, container, seed=123, depth=0)
    
    # Verify all placements stay within container bounds
    for placement in cands:
        assert all(cell in container for cell in placement.covered), \
            f"Placement {placement} has cells outside container"
        
        # Verify placement covers the target
        assert (0, 0, 0) in placement.covered, \
            f"Placement {placement} doesn't cover target (0,0,0)"

def test_no_placements_when_occupied():
    """Test that no placements are generated when target is occupied."""
    
    container = {(0, 0, 0), (1, 0, 0)}
    cells_sorted = sorted(container)
    occ = OccMask(cells_sorted)
    
    # Occupy the target cell
    occ.set_cells([(0, 0, 0)])
    
    tiny_piece = PieceDef("Z", [(0, 0, 0), (1, 0, 0)])
    lib = {"Z": tiny_piece}
    
    class MockBag:
        def to_dict(self):
            return {"Z": 1}
    
    bag = MockBag()
    
    # Should get no placements since target is occupied
    cands = for_target((0, 0, 0), occ, bag, lib, container, seed=123, depth=0)
    
    assert len(cands) == 0, "Should get no placements when target is occupied"

def test_no_placements_when_inventory_empty():
    """Test that no placements are generated when no pieces available."""
    
    container = {(0, 0, 0), (1, 0, 0)}
    cells_sorted = sorted(container)
    occ = OccMask(cells_sorted)
    
    tiny_piece = PieceDef("Z", [(0, 0, 0), (1, 0, 0)])
    lib = {"Z": tiny_piece}
    
    class MockBag:
        def to_dict(self):
            return {"Z": 0}  # No pieces available
    
    bag = MockBag()
    
    cands = for_target((0, 0, 0), occ, bag, lib, container, seed=123, depth=0)
    
    assert len(cands) == 0, "Should get no placements when no pieces available"

def test_placement_structure():
    """Test that placement objects have correct structure."""
    
    container = {(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)}
    cells_sorted = sorted(container)
    occ = OccMask(cells_sorted)
    
    tiny_piece = PieceDef("A", [(0, 0, 0), (1, 0, 0)])
    lib = {"A": tiny_piece}
    
    class MockBag:
        def to_dict(self):
            return {"A": 1}
    
    bag = MockBag()
    
    cands = for_target((0, 0, 0), occ, bag, lib, container, seed=123, depth=1)
    
    for placement in cands:
        # Check placement has required fields
        assert hasattr(placement, 'piece')
        assert hasattr(placement, 'ori_idx')
        assert hasattr(placement, 't')
        assert hasattr(placement, 'covered')
        
        # Check types
        assert isinstance(placement.piece, str)
        assert isinstance(placement.ori_idx, int)
        assert isinstance(placement.t, tuple)
        assert isinstance(placement.covered, tuple)
        assert len(placement.t) == 3
        assert all(isinstance(coord, tuple) and len(coord) == 3 for coord in placement.covered)
