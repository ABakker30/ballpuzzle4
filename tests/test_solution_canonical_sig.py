"""Test canonical solution signature under container symmetry."""

import pytest
from src.io.solution_sig import canonical_state_signature
from src.coords.symmetry_fcc import apply_rot
from src.solver.symbreak import container_symmetry_group

def test_rotated_solutions_same_signature():
    """Two rotated-equivalent final states should have identical canonical signatures."""
    # Create a simple asymmetric occupied state
    occupied_cells = {(0, 0, 0), (1, 0, 0), (0, 1, 0)}
    
    # Create a symmetric container (cube)
    container_cells = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0),
                       (0, 0, 1), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
    symGroup = container_symmetry_group(container_cells)
    
    # Get canonical signature for original state
    sig1 = canonical_state_signature(occupied_cells, symGroup)
    
    # Apply a rotation to the occupied cells
    rotation = symGroup[1]  # Use second rotation (not identity)
    rotated_cells = {apply_rot(rotation, cell) for cell in occupied_cells}
    
    # Get canonical signature for rotated state
    sig2 = canonical_state_signature(rotated_cells, symGroup)
    
    # They should be identical
    assert sig1 == sig2, f"Rotated states should have same signature: {sig1} != {sig2}"

def test_different_states_different_signatures():
    """Different occupied states should have different canonical signatures."""
    # Create two states that are NOT equivalent under symmetry
    state1 = {(0, 0, 0), (1, 0, 0)}  # Two adjacent cells along x-axis
    state2 = {(0, 0, 0), (1, 1, 0)}  # Two diagonal cells
    
    # Use same container
    container_cells = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)]
    symGroup = container_symmetry_group(container_cells)
    
    sig1 = canonical_state_signature(state1, symGroup)
    sig2 = canonical_state_signature(state2, symGroup)
    
    # They should be different (diagonal vs adjacent patterns)
    assert sig1 != sig2, f"Different states should have different signatures: {sig1} == {sig2}"

def test_empty_state_signature():
    """Empty state should have consistent signature."""
    empty_state = set()
    
    container_cells = [(0, 0, 0), (1, 0, 0)]
    symGroup = container_symmetry_group(container_cells)
    
    sig1 = canonical_state_signature(empty_state, symGroup)
    sig2 = canonical_state_signature(empty_state, symGroup)
    
    # Should be consistent
    assert sig1 == sig2
    assert isinstance(sig1, str)
    assert len(sig1) == 64  # SHA256 hex length

def test_signature_is_hex_string():
    """Signature should be a valid SHA256 hex string."""
    occupied_cells = {(0, 0, 0)}
    container_cells = [(0, 0, 0), (1, 0, 0)]
    symGroup = container_symmetry_group(container_cells)
    
    sig = canonical_state_signature(occupied_cells, symGroup)
    
    # Should be 64-character hex string
    assert isinstance(sig, str)
    assert len(sig) == 64
    assert all(c in '0123456789abcdef' for c in sig)
