from __future__ import annotations
from typing import List, Tuple, Set, Iterable
from ..coords.symmetry_fcc import ROTATIONS_24, maps_container_to_itself, canonical_atom_tuple, apply_rot

I3 = Tuple[int,int,int]
Rot = Tuple[I3,I3,I3]

def container_symmetry_group(cells: Iterable[I3]) -> List[Rot]:
    C = set(cells)
    return [R for R in ROTATIONS_24 if maps_container_to_itself(C, R)]

def anchor_rule_filter(placements: Iterable[Tuple[str, Tuple[I3,...]]],
                       min_cell: I3,
                       lowest_piece: str,
                       Rgroup: List[Rot]) -> List[Tuple[str, Tuple[I3,...]]]:
    """
    placements: iterable of (pieceId, atomCoords) in engine ints (translated)
    Enforce:
      - placement must cover min_cell
      - among same pieceId covering min_cell, only canonical orientation allowed
    """
    out = []
    seen_canon = set()
    for pid, atoms in placements:
        if pid != lowest_piece:
            continue
        if min_cell not in atoms:
            continue
        # Normalize atoms relative to min_cell to detect orientation only
        rel = tuple(sorted((x-min_cell[0], y-min_cell[1], z-min_cell[2]) for (x,y,z) in atoms))
        canon = canonical_atom_tuple(rel)
        if canon in seen_canon:
            continue
        seen_canon.add(canon)
        out.append((pid, atoms))
    return out

def is_canonical_under_container_syms(atoms: Tuple[I3,...], Rgroup: List[Rot]) -> bool:
    """Keep only canonical representative of the orbit under Rgroup."""
    orbit = []
    for R in Rgroup:
        orbit.append(tuple(sorted(apply_rot(R, p) for p in atoms)))
    return min(orbit) == tuple(sorted(atoms))
