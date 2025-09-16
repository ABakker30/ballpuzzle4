from __future__ import annotations
from typing import Dict, Tuple, Iterable

I3 = Tuple[int,int,int]

class OccMask:
    """Bitmask over a fixed ordered container cell list."""
    def __init__(self, cells: Iterable[I3]):
        self.order = {c:i for i,c in enumerate(cells)}
        self.mask = 0

    def clone(self) -> "OccMask":
        o = OccMask(self.order.keys())
        o.order = self.order
        o.mask = self.mask
        return o

    def set_cells(self, cells: Iterable[I3]) -> None:
        m = self.mask
        for c in cells:
            m |= (1 << self.order[c])
        self.mask = m

    def clear_cells(self, cells: Iterable[I3]) -> None:
        m = self.mask
        for c in cells:
            m &= ~(1 << self.order[c])
        self.mask = m

    def popcount(self) -> int:
        return self.mask.bit_count()

class SeenMasks:
    def __init__(self):
        self._seen = set()
    def check_and_add(self, mask_int: int) -> bool:
        """Return True if new, False if already seen."""
        if mask_int in self._seen: return False
        self._seen.add(mask_int); return True
