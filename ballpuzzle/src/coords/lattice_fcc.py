# src/coords/lattice_fcc.py
# Single source of truth for FCC neighbors: delegate to symmetry_fcc.
from __future__ import annotations
from typing import Tuple, Set, List
from .symmetry_fcc import NEIGHBORS as _SYM_NEIGHBORS  # 12 rhombohedral steps (engine-native)

I3 = Tuple[int, int, int]

# Re-export the exact set used everywhere else
NEIGHBORS: Set[I3] = set(_SYM_NEIGHBORS)

def is_neighbor(a: I3, b: I3) -> bool:
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    return (dx, dy, dz) in NEIGHBORS

class FCCLattice:
    """Thin adapter around the engine's rhombohedral FCC neighbor set."""
    def neighbors_relative(self) -> List[I3]:
        """Return the 12 relative neighbor step vectors."""
        return list(NEIGHBORS)

    def get_neighbors(self, p: I3) -> List[I3]:
        """Absolute neighbors of point p under the 12-step engine FCC."""
        px, py, pz = p
        return [(px + dx, py + dy, pz + dz) for (dx, dy, dz) in NEIGHBORS]
