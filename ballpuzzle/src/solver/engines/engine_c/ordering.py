"""Holes-first ordering strategy for target cell selection."""

from typing import List, Dict
from .rand import Rng


def pick_target_cell(empty_bitset: int, covers_by_cell: List[List[int]], 
                    feasible_mask: int) -> int:
    """
    Choose empty cell with fewest feasible candidates (holes-first strategy).
    
    Args:
        empty_bitset: Bitset of currently empty cells
        covers_by_cell: For each cell index, list of candidate indices covering it
        feasible_mask: Bitset of currently feasible candidates
        
    Returns:
        Cell index with minimum feasible candidates, or -1 if none
    """
    min_candidates = float('inf')
    best_cell = -1
    
    # Check all cells to find empty ones
    for cell_idx in range(len(covers_by_cell)):
        # Check if this cell is empty
        if empty_bitset & (1 << cell_idx):
            # Count feasible candidates for this empty cell
            feasible_count = 0
            for cand_idx in covers_by_cell[cell_idx]:
                if cand_idx < 64 and (feasible_mask & (1 << cand_idx)):  # Limit to 64-bit for now
                    feasible_count += 1
            
            # Update best if this cell has fewer candidates
            if feasible_count < min_candidates and feasible_count > 0:
                min_candidates = feasible_count
                best_cell = cell_idx
    
    return best_cell


def order_candidates(candidate_ids: List[int], shuffle_policy: str, 
                    rng: Rng) -> List[int]:
    """
    Order candidates with optional shuffling for tie-breaking.
    
    Args:
        candidate_ids: List of candidate indices
        shuffle_policy: "none", "ties_only", or "full"
        rng: Random number generator for shuffling
        
    Returns:
        Ordered list of candidate indices
    """
    if not candidate_ids:
        return []
    
    # Base ordering: stable sort by candidate index (deterministic)
    ordered = sorted(candidate_ids)
    
    if shuffle_policy == "none":
        return ordered
    elif shuffle_policy == "ties_only":
        # For now, treat all as ties and shuffle
        # TODO: Implement actual tie detection based on heuristic scores
        return rng.shuffle(ordered.copy())
    elif shuffle_policy == "full":
        return rng.shuffle(ordered.copy())
    else:
        raise ValueError(f"Unknown shuffle policy: {shuffle_policy}")


def compute_candidate_scores(candidate_ids: List[int], 
                           covers_by_cell: List[List[int]],
                           empty_bitset: int) -> Dict[int, int]:
    """
    Compute heuristic scores for candidates (least constraining value).
    
    Args:
        candidate_ids: List of candidate indices to score
        covers_by_cell: Coverage information for each cell
        empty_bitset: Current empty cells
        
    Returns:
        Dictionary mapping candidate_id to score (lower is better)
    """
    scores = {}
    
    for cand_id in candidate_ids:
        # Score based on how many future choices this candidate eliminates
        # Lower score = less constraining = better
        constraint_count = 0
        
        # This is a placeholder - would need actual candidate coverage data
        # For now, use candidate index as a simple heuristic
        scores[cand_id] = cand_id
    
    return scores
