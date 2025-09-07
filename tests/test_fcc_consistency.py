# tests/test_fcc_consistency.py
from src.coords.lattice_fcc import NEIGHBORS as N1
from src.coords.symmetry_fcc import NEIGHBORS as N2, ROTATIONS_24, apply_rot

def test_neighbor_sets_identical():
    assert set(N1) == set(N2)

def test_rotations_preserve_neighbors():
    S = set(N2)
    for R in ROTATIONS_24:
        assert {apply_rot(R, v) for v in S} == S

def test_rotations_count_is_24():
    assert len(ROTATIONS_24) == 24
