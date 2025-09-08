"""Interruptible search implementation for Engine-C."""

import time
from typing import Dict, List, Callable, Generator, Any
from .bitset import bitset_from_indices
from .ordering import pick_target_cell
from .pruning.disconnected import is_disconnected
from .rand import Rng


class InterruptibleSearchState:
    """State for interruptible search."""
    def __init__(self):
        self.nodes_visited = 0
        self.nodes_pruned = 0
        self.solutions_found = 0
        self.max_depth = 0
        self.start_time = time.time()
        self.last_progress_time = time.time()
        self.last_progress_nodes = 0


def interruptible_dfs_solve(
    candidates: List[int],
    covers_by_cell: List[List[int]], 
    candidate_meta: List[tuple],
    all_mask: int,
    cells_by_index: List[tuple],
    index_of_cell: Dict[tuple, int],
    inventory: Dict[str, int],
    max_results: int = 1,
    time_budget_s: float = 60.0,
    progress_interval_s: float = 1.0,
    node_limit: int = 50000
) -> Generator[Dict[str, Any], None, None]:
    """
    Interruptible DFS search that yields progress events.
    
    Yields:
        Dict: Progress events ('tick') and solution events ('solution')
    """
    state = InterruptibleSearchState()
    remaining_inventory = inventory.copy()
    
    def search_recursive(occ_bitset: int, depth: int, solution_path: List[int]) -> Generator[Dict[str, Any], None, None]:
        """Recursive search with yielding."""
        state.nodes_visited += 1
        state.max_depth = max(state.max_depth, depth)
        
        # Debug output for first few nodes
        if state.nodes_visited <= 5:
            print(f"DEBUG: Node {state.nodes_visited}, depth {depth}, occ_bitset {occ_bitset:016b}")
        
        # Check limits every 10 nodes for responsiveness (more frequent)
        if state.nodes_visited % 10 == 0:
            elapsed = time.time() - state.start_time
            
            # Time budget check
            if elapsed > time_budget_s:
                return
            
            # Node limit check (much lower limit to prevent hangs)
            if state.nodes_visited > 1000:
                return
                
            # Progress reporting
            if elapsed - state.last_progress_time >= progress_interval_s:
                yield {
                    "type": "tick",
                    "v": 1,
                    "t_ms": int(elapsed * 1000),
                    "metrics": {
                        "nodes": state.nodes_visited,
                        "depth": depth,
                        "pruned": state.nodes_pruned,
                        "solutions": state.solutions_found,
                        "elapsed_s": elapsed
                    }
                }
                state.last_progress_time = elapsed
        
        # Check if solution found
        empty_bitset = all_mask ^ occ_bitset
        if empty_bitset == 0:
            # Complete solution found
            state.solutions_found += 1
            
            # Build placements from solution path
            placements = []
            for candidate_idx in solution_path:
                piece_id, orient_idx, anchor_idx = candidate_meta[candidate_idx]
                placements.append({
                    "piece": piece_id,
                    "ori": orient_idx,
                    "t": list(cells_by_index[anchor_idx])
                })
            
            yield {
                "type": "solution",
                "v": 1,
                "t_ms": int((time.time() - state.start_time) * 1000),
                "solution": {
                    "containerCidSha256": "placeholder",
                    "lattice": "fcc", 
                    "piecesUsed": inventory,
                    "placements": placements,
                    "sid_state_sha256": "placeholder",
                    "sid_route_sha256": "placeholder",
                    "sid_state_canon_sha256": "placeholder"
                }
            }
            
            if state.solutions_found >= max_results:
                return
            return
        
        # Find target cell using holes-first ordering
        empty_bitset = all_mask ^ occ_bitset
        
        # Build feasible candidate set (don't use bitset due to size limitations)
        feasible_candidates = set()
        for candidate_idx in range(len(candidates)):
            candidate_bitset = candidates[candidate_idx]
            piece_id, _, _ = candidate_meta[candidate_idx]
            
            # Check if candidate fits and piece available
            if ((occ_bitset & candidate_bitset) == 0 and 
                remaining_inventory.get(piece_id, 0) > 0):
                feasible_candidates.add(candidate_idx)
        
        # Find target cell with manual holes-first logic since we can't use bitset
        target_cell_idx = -1
        min_feasible_count = float('inf')
        
        for cell_idx in range(len(covers_by_cell)):
            if (empty_bitset >> cell_idx) & 1:  # Cell is empty
                # Count feasible candidates for this cell
                feasible_count = 0
                for candidate_idx in covers_by_cell[cell_idx]:
                    if candidate_idx in feasible_candidates:
                        feasible_count += 1
                
                if 0 < feasible_count < min_feasible_count:
                    min_feasible_count = feasible_count
                    target_cell_idx = cell_idx
        
        # Debug output for target cell selection
        if state.nodes_visited <= 5:
            print(f"DEBUG: Target cell: {target_cell_idx}, feasible candidates: {len(feasible_candidates)}")
            if target_cell_idx >= 0:
                feasible_for_target = sum(1 for c in covers_by_cell[target_cell_idx] if c in feasible_candidates)
                print(f"DEBUG: Feasible candidates for cell {target_cell_idx}: {feasible_for_target}")
        
        if target_cell_idx == -1:
            state.nodes_pruned += 1
            if state.nodes_visited <= 5:
                print(f"DEBUG: No target cell found, pruning node {state.nodes_visited}")
            return
        
        # Try candidates for target cell
        candidates_tried = 0
        for candidate_idx in covers_by_cell[target_cell_idx]:
            candidate_bitset = candidates[candidate_idx]
            piece_id, _, _ = candidate_meta[candidate_idx]
            
            # Check if candidate is feasible
            if (candidate_idx in feasible_candidates):
                candidates_tried += 1
                
                # Debug output for first few candidates
                if state.nodes_visited <= 5 and candidates_tried <= 3:
                    print(f"DEBUG: Trying candidate {candidate_idx} (piece {piece_id}) at depth {depth}")
                
                # Apply candidate
                new_occ_bitset = occ_bitset | candidate_bitset
                remaining_inventory[piece_id] -= 1
                new_solution_path = solution_path + [candidate_idx]
                
                # Temporarily disable disconnected void pruning for debugging
                # empty_bitset = all_mask ^ new_occ_bitset
                # if not is_disconnected(empty_bitset, cells_by_index, index_of_cell):
                
                # Always recurse for now
                yield from search_recursive(new_occ_bitset, depth + 1, new_solution_path)
                
                # else:
                #     state.nodes_pruned += 1
                #     if state.nodes_visited <= 5:
                #         print(f"DEBUG: Candidate {candidate_idx} pruned due to disconnected voids")
                
                # Backtrack
                remaining_inventory[piece_id] += 1
        
        # Debug output for candidate attempts
        if state.nodes_visited <= 5:
            print(f"DEBUG: Tried {candidates_tried} candidates at node {state.nodes_visited}")
    
    # Start search
    yield from search_recursive(0, 0, [])
    
    # Final progress report
    elapsed = time.time() - state.start_time
    yield {
        "type": "done",
        "v": 1,
        "t_ms": int(elapsed * 1000),
        "metrics": {
            "solutions": state.solutions_found,
            "nodes": state.nodes_visited,
            "pruned": state.nodes_pruned,
            "bestDepth": state.max_depth,
            "smallMode": False,
            "symGroup": 1,
            "seed": 0
        }
    }
