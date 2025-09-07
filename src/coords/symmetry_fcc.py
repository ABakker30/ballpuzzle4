from __future__ import annotations
from typing import Iterable, List, Tuple, Set

I3 = Tuple[int,int,int]

# Rhombohedral FCC neighbor set (12)
NEIGHBORS: Set[I3] = {
    (1,0,0),(0,1,0),(0,0,1), (-1,1,0),(0,-1,1),(1,0,-1),
    (-1,0,0),(0,-1,0),(0,0,-1), (1,-1,0),(0,1,-1),(-1,0,1)
}

def _mat_mul_vec(M: Tuple[I3,I3,I3], v: I3) -> I3:
    x,y,z = v
    return (M[0][0]*x + M[0][1]*y + M[0][2]*z,
            M[1][0]*x + M[1][1]*y + M[1][2]*z,
            M[2][0]*x + M[2][1]*y + M[2][2]*z)

def _det3(M: Tuple[I3,I3,I3]) -> int:
    (a,b,c),(d,e,f),(g,h,i)=M
    return a*(e*i-f*h) - b*(d*i-f*g) + c*(d*h-e*g)

def _list_unique(seq):
    out, seen = [], set()
    for x in seq:
        t = tuple(sum(M,()) for M in [x])  # flatten for hash
        if t not in seen:
            seen.add(t); out.append(x)
    return out

def all_fcc_rotations() -> List[Tuple[I3,I3,I3]]:
    """Enumerate proper rotations that permute the FCC neighbor set."""
    basis = list(NEIGHBORS)
    rots = []
    for c1 in basis:
        for c2 in basis:
            for c3 in basis:
                M = ((c1[0],c2[0],c3[0]),
                     (c1[1],c2[1],c3[1]),
                     (c1[2],c2[2],c3[2]))
                if _det3(M) != 1:
                    continue
                ok = True
                for v in NEIGHBORS:
                    mv = _mat_mul_vec(M, v)
                    if mv not in NEIGHBORS:
                        ok = False; break
                if ok:
                    rots.append(M)
    # Deduplicate; should leave 24
    uniq = []
    seen = set()
    for M in rots:
        t = (M[0]+M[1]+M[2])
        if t not in seen:
            seen.add(t); uniq.append(M)
    assert len(uniq) == 24, f"Expected 24 FCC rotations, got {len(uniq)}"
    return uniq

ROTATIONS_24 = all_fcc_rotations()

def apply_rot(M: Tuple[I3,I3,I3], p: I3) -> I3:
    return _mat_mul_vec(M, p)

def canonical_atom_tuple(atoms: Iterable[I3]) -> Tuple[I3,...]:
    """Return a canonical representative of an atom set under the 24 rotations.
       Use sorted tuple of rotated atoms, then pick lexicographically minimal."""
    pts = list(atoms)
    cands = []
    for R in ROTATIONS_24:
        c = tuple(sorted(apply_rot(R, p) for p in pts))
        cands.append(c)
    return min(cands)

def maps_container_to_itself(container_cells: Set[I3], M: Tuple[I3,I3,I3]) -> bool:
    return {apply_rot(M, c) for c in container_cells} == container_cells
