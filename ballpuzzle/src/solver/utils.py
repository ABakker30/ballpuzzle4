"""Utility functions for solver operations."""

from typing import Tuple, List, Optional, Dict, Iterable, Set
from ..coords.symmetry_fcc import NEIGHBORS

I3 = Tuple[int,int,int]

def first_empty_cell(occ, cells_sorted: List[I3]) -> Optional[I3]:
    """Find the first empty cell in the sorted container cells."""
    for c in cells_sorted:
        i = occ.order[c]
        if ((occ.mask >> i) & 1) == 0:
            return c
    return None

# NEW: simple support count under gravity (dz = -1)
# Downward-step set in rhombohedral FCC are neighbors with dz == -1
_DOWN_STEPS = tuple(v for v in NEIGHBORS if v[2] == -1)

def support_contacts(covered: Iterable[I3], occupied: Set[I3]) -> int:
    """Count how many cells in covered have downward neighbors in occupied set."""
    cnt = 0
    for c in covered:
        for dx,dy,dz in _DOWN_STEPS:
            if (c[0]+dx, c[1]+dy, c[2]+dz) in occupied:
                cnt += 1
                break
    return cnt

def index_map(cells_sorted: List[I3]) -> Dict[I3, int]:
    """Create mapping from cell coordinates to bit indices.
    
    Args:
        cells_sorted: List of cells in sorted order
        
    Returns:
        Dictionary mapping cell to its bit index
    """
    return {cell: i for i, cell in enumerate(cells_sorted)}
