"""DFS search core with budgets, hooks, and pruning."""

import time
from typing import List, Dict, Callable, Optional, Tuple
from .bitset import bitset_intersects, bitset_difference, popcount
from .ordering import pick_target_cell, order_candidates
from .pruning.disconnected import is_disconnected
from .rand import Rng


class SearchState:
    """Search state tracking for DFS."""
    
    def __init__(self):
        self.occ_bitset = 0
        self.depth = 0
        self.solutions_found = 0
        self.nodes_visited = 0
        self.nodes_pruned = 0
        self.start_time = time.time()
        self.last_progress_time = time.time()
        self.last_progress_nodes = 0


def dfs_solve(
    candidates: List[int],
    covers_by_cell: List[List[int]], 
    candidate_meta: List[Tuple[str, int, int]],
    all_mask: int,
    cells_by_index: List,
    index_of_cell: Dict,
    inventory: Dict[str, int],
    max_results: int,
    time_budget_s: float,
    pruning_level: str,
    shuffle_policy: str,
    rng: Rng,
    snapshot_every_nodes: int,
    on_solution: Callable,
    on_progress: Callable,
    cancel_flag: Optional[Callable[[], bool]] = None
) -> Dict:
    """
    Core DFS search with all Engine-C optimizations.
    
    Args:
        candidates: List of candidate bitsets
        covers_by_cell: Coverage mapping
        candidate_meta: Metadata for each candidate
        all_mask: Bitset with all container cells set
        cells_by_index: Index to coordinate mapping
        index_of_cell: Coordinate to index mapping
        inventory: Piece inventory counts
        max_results: Maximum solutions to find
        time_budget_s: Time limit in seconds
        pruning_level: "none", "basic", or "full"
        shuffle_policy: "none", "ties_only", or "full"
        rng: Random number generator
        snapshot_every_nodes: Progress reporting interval
        on_solution: Solution callback
        on_progress: Progress callback
        cancel_flag: Cancellation check function
        
    Returns:
        Search statistics dictionary
    """
    state = SearchState()
    remaining_inventory = inventory.copy()
    
    def search_recursive(occ_bitset: int, depth: int, solution_path: List[int] = None) -> bool:
        """Recursive DFS implementation."""
        if solution_path is None:
            solution_path = []
        
        state.nodes_visited += 1
        state.depth = max(state.depth, depth)
        
        # Budget and cancellation checks every K nodes
        if state.nodes_visited % 1000 == 0:  # Check more frequently
            elapsed = time.time() - state.start_time
            
            # Time budget check
            if elapsed > time_budget_s:
                return True  # Stop search
            
            # Node limit check (safety for large inventories)
            if state.nodes_visited > 50000:  # Hard limit to prevent lockups
                return True  # Stop search
            
            # Cancellation check
            if cancel_flag and cancel_flag():
                return True  # Stop search
        
        # Progress reporting - yield control to allow interruption
        if (state.nodes_visited - state.last_progress_nodes >= snapshot_every_nodes):
            elapsed = time.time() - state.start_time
            should_continue = on_progress(state.nodes_visited, depth, elapsed)
            state.last_progress_nodes = state.nodes_visited
            
            # Allow engine to be halted by returning False from progress callback
            if should_continue is False:
                return True  # Stop search
        
        # Check if solution found
        empty_bitset = all_mask ^ occ_bitset
        if empty_bitset == 0:
            # Build solution from used candidates
            solution_placements = []
            for cand_idx in solution_path:
                piece_id, orient_idx, anchor_idx = candidate_meta[cand_idx]
                anchor_cell = cells_by_index[anchor_idx]
                
                # Get the oriented piece cells
                from .precompute import get_static_orientations
                orientations = get_static_orientations(piece_id)
                if orient_idx < len(orientations):
                    oriented_cells = orientations[orient_idx]
                    if oriented_cells:
                        # Calculate translation to place first cell at anchor
                        ref_cell = oriented_cells[0]
                        translation = (
                            anchor_cell[0] - ref_cell[0],
                            anchor_cell[1] - ref_cell[1],
                            anchor_cell[2] - ref_cell[2]
                        )
                        
                        # Apply translation to all cells
                        final_coords = []
                        for px, py, pz in oriented_cells:
                            final_coords.append([
                                px + translation[0],
                                py + translation[1],
                                pz + translation[2]
                            ])
                        
                        placement = {
                            "piece": piece_id,
                            "ori": orient_idx,
                            "t": list(anchor_cell),
                            "coordinates": final_coords
                        }
                        solution_placements.append(placement)
            
            on_solution(solution_placements)
            state.solutions_found += 1
            
            # Stop if we've found enough solutions
            if state.solutions_found >= max_results:
                return True
            return False
        
        # Pick target cell using holes-first strategy
        feasible_mask = compute_feasible_candidates(
            candidates, occ_bitset, remaining_inventory, candidate_meta
        )
        
        if feasible_mask == 0:
            state.nodes_pruned += 1
            return False  # No feasible candidates at all
        
        target_cell = pick_target_cell(empty_bitset, covers_by_cell, feasible_mask)
        if target_cell == -1:
            state.nodes_pruned += 1
            return False  # No valid target cell
        
        # Get candidates covering target cell
        covering_candidates = []
        for cand_idx in covers_by_cell[target_cell]:
            if cand_idx < len(candidates) and (feasible_mask & (1 << cand_idx)):
                covering_candidates.append(cand_idx)
        
        if not covering_candidates:
            state.nodes_pruned += 1
            return False  # No feasible candidates
        
        # Order candidates
        ordered_candidates = order_candidates(covering_candidates, shuffle_policy, rng)
        
        # Try each candidate
        for cand_idx in ordered_candidates:
            if cand_idx >= len(candidates):
                continue
                
            cand_bitset = candidates[cand_idx]
            
            # Check for overlap
            if bitset_intersects(occ_bitset, cand_bitset):
                continue
            
            # Check inventory before applying
            piece_id, _, _ = candidate_meta[cand_idx]
            if remaining_inventory.get(piece_id, 0) <= 0:
                continue
            
            # Apply candidate
            new_occ = occ_bitset | cand_bitset
            
            # Pruning checks (temporarily disabled for debugging)
            # if pruning_level != "none":
            #     new_empty = all_mask ^ new_occ
            #     if is_disconnected(new_empty, cells_by_index, index_of_cell):
            #         state.nodes_pruned += 1
            #         continue
            
            # Update inventory
            remaining_inventory[piece_id] -= 1
            
            # Recurse with updated solution path
            new_solution_path = solution_path + [cand_idx]
            should_stop = search_recursive(new_occ, depth + 1, new_solution_path)
            
            # Restore inventory
            remaining_inventory[piece_id] += 1
            
            if should_stop:
                return True
        
        return False
    
    # Start search
    search_recursive(0, 0, [])
    
    # Return statistics
    elapsed = time.time() - state.start_time
    return {
        "solutions": state.solutions_found,
        "nodes": state.nodes_visited,
        "pruned": state.nodes_pruned,
        "bestDepth": state.depth,
        "elapsed_s": elapsed
    }


def compute_feasible_candidates(
    candidates: List[int],
    occ_bitset: int, 
    inventory: Dict[str, int],
    candidate_meta: List[Tuple[str, int, int]]
) -> int:
    """Compute bitset of currently feasible candidates."""
    feasible = 0
    
    for i, cand_bitset in enumerate(candidates):
        # Check inventory
        piece_id, _, _ = candidate_meta[i]
        if inventory.get(piece_id, 0) <= 0:
            continue
        
        # Check overlap
        if bitset_intersects(occ_bitset, cand_bitset):
            continue
        
        feasible |= (1 << i)
    
    return feasible


def build_solution_placements(used_candidates: List[int], 
                            candidate_meta: List[Tuple[str, int, int]]) -> List[Dict]:
    """Build solution placements from list of used candidate indices."""
    placements = []
    
    for cand_idx in used_candidates:
        if cand_idx < len(candidate_meta):
            piece_id, orient_idx, anchor_idx = candidate_meta[cand_idx]
            placements.append({
                "piece": piece_id,
                "ori": orient_idx,
                "t": [anchor_idx, 0, 0]  # Simplified translation
            })
    
    return placements
