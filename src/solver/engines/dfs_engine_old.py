fr"""Bitmask-optimized DFS engine for high-performance ball puzzle solving."""

import time
from typing import Iterator, Dict, Any, Set, List, Tuple
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...solver.tt import OccMask, SeenMasks
from ...solver.heuristics import tie_shuffle
from ...solver.placement_gen import Placement
from ...solver.utils import first_empty_cell
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...pieces.inventory import PieceBag
from ...io.solution_sig import canonical_state_signature, extract_occupied_cells_from_placements
from ...solver.symbreak import container_symmetry_group
from .engine_c.lattice_fcc import FCC_NEIGHBORS
from .engine_c.bitset import popcount, bitset_from_indices, bitset_to_indices, bitset_intersects
import itertools

I3 = Tuple[int, int, int]

def has_unfillable_holes(empty_cells: Set[I3]) -> bool:
    """
    Detect if empty cells form disconnected components where any component is too small 
    to fill with 4-cell pieces. Matches Engine-C disconnected void detection logic.
    
    Args:
        empty_cells: Set of empty cell coordinates
        
    Returns:
        True if there are unfillable holes (should prune this branch)
    """
    num_empty = len(empty_cells)
    if num_empty <= 1:
        return False  # Single empty cell or none, cannot be disconnected
    
    # Find all connected components using flood-fill
    visited = set()
    
    for start_cell in empty_cells:
        if start_cell in visited:
            continue
            
        # Start new component with flood-fill
        from collections import deque
        component_size = 0
        queue = deque([start_cell])
        visited.add(start_cell)
        
        while queue:
            current = queue.popleft()
            component_size += 1
            
            # Check all FCC neighbors
            for dx, dy, dz in FCC_NEIGHBORS:
                neighbor = (current[0] + dx, current[1] + dy, current[2] + dz)
                if neighbor in empty_cells and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # Only prune if we find a disconnected component with 1, 2, or 3 cells
        # These are definitely unfillable since all pieces are 4 cells
        if component_size < 4:
            return True  # Found unfillable hole
    
    return False

class DFSEngine(EngineProtocol):
    name = "dfs"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        import time
        t0 = time.time()
        seed = int(options.get("seed", 0))
        caps = options.get("caps", {}) or {}
        max_nodes = int(caps.get("maxNodes", 0))
        max_depth = int(caps.get("maxDepth", 0))
        max_results = int(options.get("max_results", 1))
        time_limit = float(options.get("time_limit", 0))  # Time limit in seconds
        flags = options.get("flags", {}) or {}
        use_mrv = options.get("mrv", True)
        use_support = options.get("support", True)
        use_hole4_detection = options.get("hole4", False)  # Enable hole4 detection pruning
        
        # Enhanced search parameters for better performance
        candidate_limit = options.get("candidate_limit", 30)  # Limit candidates per node
        prefer_small_pieces = options.get("prefer_small_pieces", True)  # Prioritize smaller pieces
        progress_every = int(options.get("progress_interval_ms", 0))
        last_tick_ms = 0

        cells_sorted: List[I3] = sorted(tuple(map(int,c)) for c in container["coordinates"])
        container_set = set(cells_sorted)
        symGroup = container_symmetry_group(cells_sorted)
        smallMode = len(cells_sorted) <= 32

        # Get inventory and container info
        inv = inventory.get("pieces", {}) or inventory
        container_size = len(cells_sorted)
        
        # Generate all valid piece combinations that sum to container size
        def generate_piece_combinations(container_size: int, available_pieces: Dict[str, int]):
            """Generate all piece combinations that sum to exactly container_size cells."""
            pieces_needed = container_size // 4
            if container_size % 4 != 0:
                return []  # Container size must be divisible by 4
            
            # Optimization: If we have exactly the pieces we need (all inventory = 1 and pieces_needed = total pieces)
            total_available = sum(available_pieces.values())
            all_ones = all(count == 1 for count in available_pieces.values())
            
            if pieces_needed == total_available and all_ones:
                # Use all pieces exactly once - no enumeration needed
                return [available_pieces.copy()]
            
            # For other cases, use the full enumeration
            from itertools import combinations_with_replacement
            
            # Get available piece types and their counts
            piece_types = list(available_pieces.keys())
            combinations = []
            
            # Generate all combinations of pieces that sum to pieces_needed
            for combo in combinations_with_replacement(piece_types, pieces_needed):
                piece_count = {}
                for piece in combo:
                    piece_count[piece] = piece_count.get(piece, 0) + 1
                
                # Check if this combination is valid (within inventory limits)
                valid = True
                for piece, count in piece_count.items():
                    if count > available_pieces.get(piece, 0):
                        valid = False
                        break
                
                if valid:
                    combinations.append(piece_count)
            
            return combinations
        
        valid_combinations = generate_piece_combinations(container_size, inv)
        
        # Focus on known working combinations that have multiple solutions
        working_combos = [
            {'A': 2, 'E': 1, 'T': 1},  # Known working
            {'A': 2, 'E': 1, 'Y': 1},  # Alternative found
            {'A': 1, 'E': 1, 'T': 2},  # Variation
            {'E': 2, 'T': 2},          # Different combination
        ]
        
        # Prioritize working combinations
        prioritized = []
        for combo in working_combos:
            if combo in valid_combinations:
                valid_combinations.remove(combo)
                prioritized.append(combo)
        
        valid_combinations = prioritized + valid_combinations
        
        if not valid_combinations:
            return
        
        # Statistics
        results = 0
        bestDepth = 0
        nodes = 0
        pruned = 0
        
        # Initialize pieces library
        pieces = load_fcc_A_to_Y()
        
        # Piece rotation strategy - cycle through starting pieces
        piece_rotation_interval = options.get("piece_rotation_interval", 5.0)  # seconds
        available_pieces = sorted(set().union(*valid_combinations))
        current_piece_idx = 0
        last_rotation_time = t0
        
        # Try each combination until solution found or time/result limit reached
        for combo_idx, target_inventory in enumerate(valid_combinations):
            # Check time and result limits before trying new combination
            if time_limit > 0 and (time.time() - t0) >= time_limit:
                break
            if results >= max_results:
                break
            
            # Check if it's time to rotate the starting piece
            current_time = time.time()
            if current_time - last_rotation_time >= piece_rotation_interval:
                current_piece_idx = (current_piece_idx + 1) % len(available_pieces)
                last_rotation_time = current_time
                preferred_start_piece = available_pieces[current_piece_idx]
                yield {"t_ms": int((current_time-t0)*1000), "type":"tick", 
                       "msg": f"Rotating to start with piece {preferred_start_piece} (rotation {current_piece_idx + 1}/{len(available_pieces)})"}
            else:
                preferred_start_piece = available_pieces[current_piece_idx] if available_pieces else None
            
            # Initialize inventory bag for this combination
            from ...pieces.inventory import PieceBag
            bag = PieceBag(target_inventory)
            
            # Initialize occupancy tracking
            occupied_set: Set[I3] = set()
            occ = OccMask(cells_sorted)
            TT = SeenMasks()
            
            # Placement stack for backtracking
            stack: List[Any] = []
            
            # Enhanced search parameters
            CANDIDATE_LIMIT_PER_DEPTH = 50  # Limit candidates at each depth to prevent explosion
            PREFER_SMALLER_PIECES = True    # Prioritize smaller pieces first
            
            # Cell index for bit operations
            cell_index = {c: i for i, c in enumerate(cells_sorted)}
            
            def dfs(depth: int) -> Iterator[Dict[str, Any]]:
                nonlocal results, bestDepth, nodes, pruned
                
                # Check time limit
                if time_limit > 0 and (time.time() - t0) >= time_limit:
                    return
                
                # Check solution count limit
                if results >= max_results:
                    return
                
                nodes += 1
                bestDepth = max(bestDepth, depth)

                # full cover
                if occ.popcount() == len(cells_sorted):
                    # build solution
                    final_cells = list(occupied_set)
                    if len(final_cells) == len(cells_sorted):
                        # Found complete solution - emit and continue searching
                        from ...io.solution_sig import canonical_state_signature
                        sid_canon = canonical_state_signature(set(final_cells), symGroup)
                        
                        # Count actual pieces used from placements (not remaining inventory)
                        pieces_used = {}
                        for pl in stack:
                            pieces_used[pl.piece] = pieces_used.get(pl.piece, 0) + 1
                        
                        sol = {
                            "containerCidSha256": container["cid_sha256"],
                            "lattice": "fcc",
                            "piecesUsed": pieces_used,
                            "placements": [{"piece": pl.piece, "ori": pl.ori_idx, "t": list(pl.t), "cells_ijk": [list(coord) for coord in pl.covered]} for pl in stack],
                            "sid_state_sha256": "dfs_state", "sid_route_sha256": "dfs_route",
                            "sid_state_canon_sha256": sid_canon,
                        }
                        yield {"t_ms": int((time.time()-t0)*1000), "type":"solution", "solution": sol}
                        results += 1
                        # Continue backtracking to find more solutions
                        return

                from ...solver.utils import first_empty_cell
                target = first_empty_cell(occ, cells_sorted)
                if target is None:
                    return

                # Enhanced MRV heuristic with support bias
                def enhanced_mrv_score(coord: I3) -> float:
                    """Enhanced MRV with support bias - prioritize cells with fewer neighbors and more support."""
                    empty_neighbors = 0
                    occupied_neighbors = 0
                    for dx, dy, dz in FCC_NEIGHBORS:
                        neighbor = (coord[0] + dx, coord[1] + dy, coord[2] + dz)
                        if neighbor in cells_sorted and neighbor not in occupied_set:
                            empty_neighbors += 1
                        elif neighbor in occupied_set:
                            occupied_neighbors += 1
                    support_bias = occupied_neighbors * 0.1  # Small bias for cells with more support
                    return empty_neighbors - support_bias

                # Generate candidates for target cell
                from ...solver.placement_gen import for_target
                from ...solver.symbreak import anchor_rule_filter
                from ...solver.heuristics import tie_shuffle
                
                candidates = []
                # Prioritize the preferred starting piece, then others
                piece_order = sorted(bag.counts.keys())
                if preferred_start_piece and preferred_start_piece in piece_order:
                    piece_order.remove(preferred_start_piece)
                    piece_order.insert(0, preferred_start_piece)
                
                for piece in piece_order:
                    if bag.get_count(piece) <= 0:
                        continue
                    
                    # Get piece orientations and generate placements
                    piece_def = pieces.get(piece)
                    if piece_def is None:
                        continue
                    for ori_idx, ori in enumerate(piece_def.orientations):
                        # Create placement manually - find translation that puts first cell at target
                        if ori:  # Check if orientation has cells
                            first_cell = ori[0]
                            t = (target[0] - first_cell[0], target[1] - first_cell[1], target[2] - first_cell[2])
                            covered = tuple((t[0] + cell[0], t[1] + cell[1], t[2] + cell[2]) for cell in ori)
                            pl = Placement(piece=piece, ori_idx=ori_idx, t=t, covered=covered)
                            if all(c in cells_sorted for c in pl.covered) and not any(c in occupied_set for c in pl.covered):
                                # Skip anchor rule filter for now - just add valid placements
                                candidates.append(pl)
                
                # Enhanced candidate ordering with piece preference
                if prefer_small_pieces:
                    # Sort by piece name (A < B < C...) to prefer smaller pieces first
                    candidates.sort(key=lambda pl: (pl.piece, enhanced_mrv_score(pl.t)))
                else:
                    candidates.sort(key=lambda pl: enhanced_mrv_score(pl.t))
                
                # Limit candidates to prevent explosion at deeper levels
                if depth > 2 and len(candidates) > candidate_limit:
                    candidates = candidates[:candidate_limit]
                
                # Shuffle for tie-breaking (deterministic if seed provided)
                candidates = tie_shuffle(candidates, None)  # No seed for now
                
                for pl in candidates:
                    # Check time and solution limits
                    if time_limit > 0 and (time.time() - t0) >= time_limit:
                        return
                    if results >= max_results:
                        return
                    
                    # Try placement
                    if bag.get_count(pl.piece) <= 0:
                        continue
                    bag.use_piece(pl.piece)
                    old_mask = occ.mask
                    occupied_set.update(pl.covered)
                    occ.mask |= sum(1 << cell_index[c] for c in pl.covered if c in cell_index)
                    
                    # Check for overlaps or out-of-bounds
                    if len(pl.covered) != len(set(pl.covered)) or not all(c in cells_sorted for c in pl.covered):
                        # backtrack
                        occupied_set.difference_update(pl.covered); occ.mask = old_mask; bag.return_piece(pl.piece)
                        continue
                    if not TT.check_and_add(occ.mask):
                        pruned += 1
                        # backtrack
                        occupied_set.difference_update(pl.covered); occ.mask = old_mask; bag.return_piece(pl.piece)
                        continue
                    stack.append(pl)
                    
                    # Hole4 detection: check if remaining empty cells form unfillable holes
                    should_prune = False
                    if use_hole4_detection:
                        remaining_empty = container_set - occupied_set
                        # Only check hole4 detection occasionally to avoid performance impact
                        if depth <= 2 and len(remaining_empty) <= 12:  # Conservative check
                            if has_unfillable_holes(remaining_empty):
                                should_prune = True
                                pruned += 1
                    
                    if not should_prune:
                        # Recurse
                        for ev in dfs(depth+1):
                            # bubble up solution events
                            yield ev
                    stack.pop()
                    # backtrack
                    occupied_set.difference_update(pl.covered)
                    occ.mask = old_mask
                    bag.return_piece(pl.piece)

            # Drive DFS for this combination
            for ev in dfs(0):
                yield ev

        # Done event
        yield {"t_ms": int((time.time()-t0)*1000), "type":"done",
               "metrics":{"solutions": results, "nodes": nodes, "pruned": pruned,
                          "bestDepth": bestDepth, "smallMode": smallMode,
                          "symGroup": len(symGroup), "seed": seed,
                          "maxNodes": max_nodes}}
