"""Placement generator for real piece placements in DFS engine."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set
from ..solver.heuristics import tie_shuffle
from ..solver.symbreak import anchor_rule_filter, container_symmetry_group

I3 = Tuple[int, int, int]

@dataclass(frozen=True)
class Placement:
    """A placement of a piece at a specific position and orientation."""
    piece: str
    ori_idx: int
    t: I3  # Translation vector
    covered: Tuple[I3, ...]  # Cells covered by this placement

def for_target(target: I3, occ, bag, lib: Dict[str, object], container_set: Set[I3], seed: int, depth: int) -> List[Placement]:
    """Generate all valid placements that cover the target cell.
    
    Args:
        target: Target cell that must be covered
        occ: OccMask tracking occupied cells
        bag: PieceBag with available piece counts
        lib: Dictionary of PieceDef objects
        container_set: Set of valid container cells
        seed: Random seed for tie-shuffle
        depth: Current search depth (for anchor rule at depth 0)
        
    Returns:
        List of valid placements covering the target cell
    """
    cands: List[Placement] = []
    
    # Generate candidates for each available piece
    for pid, count in bag.to_dict().items():
        if count <= 0:
            continue
            
        pdef = lib.get(pid)
        if not pdef:
            continue
            
        # Try each orientation of the piece
        for oi, orient in enumerate(pdef.orientations):
            # Try each atom as the anchor to land on target
            for atom in orient:
                # Calculate translation to place this atom at target
                dx = target[0] - atom[0]
                dy = target[1] - atom[1] 
                dz = target[2] - atom[2]
                
                # Check if all atoms fit in container and are unoccupied
                covered_cells = []
                valid = True
                
                for u in orient:
                    cell = (u[0] + dx, u[1] + dy, u[2] + dz)
                    
                    # Check if cell is in container
                    if cell not in container_set:
                        valid = False
                        break
                        
                    # Check if cell is already occupied
                    if hasattr(occ, 'order') and cell in occ.order:
                        cell_idx = occ.order[cell]
                        if (occ.mask >> cell_idx) & 1:
                            valid = False
                            break
                    else:
                        # Fallback if occ doesn't have order attribute
                        valid = False
                        break
                        
                    covered_cells.append(cell)
                
                if not valid:
                    continue
                    
                # Create placement
                placement = Placement(
                    piece=pid,
                    ori_idx=oi,
                    t=(dx, dy, dz),
                    covered=tuple(sorted(covered_cells))
                )
                cands.append(placement)
    
    # Apply anchor rule filter at depth 0
    if depth == 0 and cands:
        min_cell = target
        
        # Convert to (pid, atoms) format for anchor_rule_filter
        packs = [(pl.piece, pl.covered) for pl in cands]
        
        # Get lowest piece ID for anchor rule
        lowest_piece = min(pl.piece for pl in cands) if cands else ""
        
        # Apply anchor rule filter
        symgroup = container_symmetry_group(list(container_set))
        kept = anchor_rule_filter(packs, min_cell, lowest_piece, symgroup)
        
        # Rebuild candidates list with only those that survived filtering
        kept_keys = set((k[0], tuple(sorted(k[1]))) for k in kept)
        cands = [pl for pl in cands if (pl.piece, pl.covered) in kept_keys]
    
    # Apply tie-shuffle for deterministic ordering
    return tie_shuffle(cands, seed)
