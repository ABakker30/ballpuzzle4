"""DLX Engine with piece combination iteration for exact cover solving."""

from typing import Iterator, Dict, List, Set, Any, Tuple, Optional
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...pieces.sphere_orientations import get_piece_orientations
from ...coords.symmetry_fcc import canonical_atom_tuple
from ...solver.heuristics import tie_shuffle
import random
from ..engine_api import EngineProtocol
from .coordinate_mapper import CoordinateMapper
from .bitmap_state import BitmapState

I3 = Tuple[int, int, int]

class DLXEngine(EngineProtocol):
    name = "dlx"
    
    def solve(self, container: List[I3], inventory, pieces, options) -> Iterator[Dict[str, Any]]:
        """Solve using Algorithm X with Dancing Links, iterating through piece combinations."""
        
        seed = options.get("seed", 42)
        max_rows_cap = options.get("max_rows_cap")
        time_limit_seconds = options.get("time_limit_seconds", None)  # Match CLI parameter name
        max_results = options.get("max_results", float('inf'))  # Allow unlimited solutions by default
        
        # print(f"DLX DEBUG: Time limit parameter: {time_limit_seconds}")
        
        rnd = random.Random(seed)
        
        def maybe_tick(**kwargs):
            nonlocal last_tick_ms
            import time
            now_ms = int(time.time() * 1000)
            if now_ms - last_tick_ms >= 100:
                last_tick_ms = now_ms
                # Check time limit during tick
                if time_limit_seconds and (time.time() - start_time) >= time_limit_seconds:
                    # print(f"DLX DEBUG: Time limit reached during tick after {time.time() - start_time:.1f} seconds")
                    raise StopIteration("Time limit reached")
                yield {"type": "tick", "data": kwargs}
        
        # Extract coordinates from container dict if needed
        if isinstance(container, dict) and "coordinates" in container:
            container_coords = [tuple(coord) for coord in container["coordinates"]]
        elif isinstance(container, (list, tuple)):
            container_coords = [tuple(coord) for coord in container]
        else:
            container_coords = []
        
        container_set = set(container_coords)
        cells_sorted = sorted(container_coords)
        
        # Initialize coordinate mapper for integer-based operations
        mapper = CoordinateMapper()
        
        # Pre-map all container coordinates
        container_coord_ids = mapper.map_coordinates(container_coords)
        # print(f"DLX DEBUG: Mapped {len(container_coords)} container coordinates to integers")
        
        last_tick_ms = 0
        results = 0
        
        # Track start time for time limit
        import time
        start_time = time.time()
        
        # Build column IDs (mapped container coordinates)
        cell_col_ids = container_coord_ids
        cell_index: Dict[I3, int] = {c: i for i, c in enumerate(cells_sorted)}
        
        inv = inventory.get("pieces", {}) or inventory
        container_size = len(cells_sorted)
        
        # Generate all valid piece combinations that sum to container size
        def generate_piece_combinations(container_size: int, available_pieces: Dict[str, int]):
            """Generate all piece combinations that sum to exactly container_size cells."""
            from itertools import combinations_with_replacement
            
            pieces_needed = container_size // 4
            if container_size % 4 != 0:
                return []
            
            piece_names = list(available_pieces.keys())
            combinations = []
            
            for combo in combinations_with_replacement(piece_names, pieces_needed):
                piece_count = {}
                for piece in combo:
                    piece_count[piece] = piece_count.get(piece, 0) + 1
                
                valid = True
                for piece, count in piece_count.items():
                    if count > available_pieces.get(piece, 0):
                        valid = False
                        break
                
                if valid:
                    combinations.append(piece_count)
            
            return combinations
        
        valid_combinations = generate_piece_combinations(container_size, inv)
        print(f"DLX DEBUG: Container size: {container_size}, Inventory: {inv}")
        print(f"DLX DEBUG: Found {len(valid_combinations)} valid piece combinations")
        
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
        print(f"DLX DEBUG: Prioritizing {len(prioritized)} known working combinations")
        
        # Use all combinations for finding multiple solutions
        # print(f"DLX DEBUG: Generated {len(valid_combinations)} valid piece combinations")
        if not valid_combinations:
            # print("DLX DEBUG: No valid piece combinations found!")
            return
        
        # Try each combination until solution found or time limit reached
        for combo_idx, target_inventory in enumerate(valid_combinations):
            target_pieces = list(target_inventory.keys())
            # print(f"DLX DEBUG: Testing combination {combo_idx+1}/{len(valid_combinations)}: {target_inventory}")
            # print(f"DLX DEBUG: Starting candidate generation at {time.time() - start_time:.2f}s")
            
            # Generate candidates for this combination
            # Build rows (piece placements) and their column sets
            rows_cols: Dict[int, Set[int]] = {}
            rows_meta: Dict[int, Dict[str, Any]] = {}
            seen_canon: Set[Tuple[str, Tuple[I3, ...]]] = set()
            best_per_cellset: Dict[frozenset, Tuple[Tuple[int, int, int], str]] = {}
            
            # Candidate budget and prioritization strategy
            CANDIDATE_BUDGET = 800  # Maximum candidates per combination
            candidates_generated = 0
            
            # Sort pieces by constraint level (fewer orientations = higher priority)
            piece_priorities = []
            for pid in target_pieces:
                try:
                    orientations = get_piece_orientations(pid)
                    orientation_count = len([o for o in orientations if o])
                    piece_priorities.append((orientation_count, pid))  # Sort by orientation count (ascending)
                except KeyError:
                    piece_priorities.append((1, pid))
            
            piece_priorities.sort()  # Most constrained pieces first
            prioritized_pieces = [pid for _, pid in piece_priorities]
            
            # Pre-calculate container boundaries for efficient position prioritization
            x_coords = [c[0] for c in container_coords]
            y_coords = [c[1] for c in container_coords]
            z_coords = [c[2] for c in container_coords]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            z_min, z_max = min(z_coords), max(z_coords)
            
            # Sort container positions by constraint level (corners first, then edges, then center)
            def position_priority(coord):
                x, y, z = coord
                # Count how many coordinates are at container boundaries
                boundary_count = 0
                if x == x_min or x == x_max:
                    boundary_count += 1
                if y == y_min or y == y_max:
                    boundary_count += 1
                if z == z_min or z == z_max:
                    boundary_count += 1
                return -boundary_count  # Negative for descending sort (corners first)
            
            prioritized_positions = sorted(container_coords, key=position_priority)
            
            # print(f"DLX DEBUG: Prioritized pieces: {piece_priorities}")
            # print(f"DLX DEBUG: Candidate budget: {CANDIDATE_BUDGET}")
            # print(f"DLX DEBUG: Position sorting complete at {time.time() - start_time:.2f}s")
            
            # Generate candidates with budget and prioritization
            for pid in prioritized_pieces:
                # print(f"DLX DEBUG: Processing piece {pid} at {time.time() - start_time:.2f}s")
                if candidates_generated >= CANDIDATE_BUDGET:
                    print(f"DLX DEBUG: Candidate budget reached ({CANDIDATE_BUDGET}), stopping generation")
                    break
                    
                if target_inventory.get(pid, 0) <= 0:
                    continue
                
                try:
                    orientations = get_piece_orientations(pid)
                except KeyError:
                    orientations = [[[0, 0, 0]]]
                
                piece_candidates_start = candidates_generated
                
                for oi, orient in enumerate(orientations):
                    if candidates_generated >= CANDIDATE_BUDGET:
                        break
                    if not orient:
                        continue
                    anchor = orient[0]
                    
                    for c in prioritized_positions:
                        if candidates_generated >= CANDIDATE_BUDGET:
                            break
                            
                        # Ensure coordinates are integers
                        c_int = (int(c[0]), int(c[1]), int(c[2]))
                        anchor_int = (int(anchor[0]), int(anchor[1]), int(anchor[2]))
                        dx, dy, dz = c_int[0] - anchor_int[0], c_int[1] - anchor_int[1], c_int[2] - anchor_int[2]
                        cov = tuple(sorted((u[0] + dx, u[1] + dy, u[2] + dz) for u in orient))
                        
                        if any(cc not in container_set for cc in cov):
                            continue
                        
                        canon = canonical_atom_tuple(cov)
                        key = (pid, canon)
                        if key in seen_canon:
                            continue
                        seen_canon.add(key)
                        
                        # Map coordinates to integer IDs
                        try:
                            coord_ids = mapper.map_coordinates(list(cov))
                            cellset = frozenset(coord_ids)
                        except KeyError:
                            continue
                        
                        # Create row using mapper
                        row_key = f"{pid}|o{oi}|t{dx},{dy},{dz}"
                        row_id = mapper.map_row(row_key, pid, oi, (dx, dy, dz), list(cov))
                        best_per_cellset[cellset] = ((0, 0, 0), row_id)
                        
                        candidates_generated += 1
                        if max_rows_cap and candidates_generated >= max_rows_cap:
                            break
                
                piece_candidates = candidates_generated - piece_candidates_start
                # print(f"DLX DEBUG: Generated {piece_candidates} candidates for piece {pid}")
                
                # Check time limit during candidate generation
                if time_limit_seconds:
                    elapsed = time.time() - start_time
                    remaining = time_limit_seconds - elapsed
                    # print(f"DLX DEBUG: Time budget: {time_limit_seconds}s, elapsed: {elapsed:.1f}s, remaining: {remaining:.1f}s")
                    if elapsed >= time_limit_seconds:
                        # print(f"DLX DEBUG: Time limit reached during candidate generation after {elapsed:.1f} seconds")
                        raise StopIteration("Time limit reached")
            
            rowsBuilt = candidates_generated
            
            # Finalize rows for this combination
            piece_candidate_counts = {}
            for cellset, (_score, row_id) in best_per_cellset.items():
                # Get placement info from mapper
                placement_info = mapper.get_placement_info(row_id)
                pid = placement_info["piece_id"]
                oi = placement_info["orientation_idx"]
                position = placement_info["position"]
                covered_cells = placement_info["coordinates"]
                
                meta = {"piece": pid, "ori": oi, "t": position, "covered": covered_cells}
                
                rows_cols[row_id] = cellset
                rows_meta[row_id] = meta
                piece_candidate_counts[pid] = piece_candidate_counts.get(pid, 0) + 1
            
            # print(f"DLX DEBUG: Candidate generation complete at {time.time() - start_time:.2f}s")
            # print(f"DLX DEBUG: Generated {len(rows_cols)} candidates for combination")
            # for pid in sorted(piece_candidate_counts.keys()):
            #     print(f"DLX DEBUG: Piece {pid}: {piece_candidate_counts[pid]} candidates")
            
            if not rows_cols:
                # print("DLX DEBUG: No candidates for this combination, trying next")
                continue
            
            # Algorithm X setup with bitmap optimization
            num_columns = len(cell_col_ids)
            num_rows = len(rows_cols)
            
            # Create bitmap state for efficient operations
            bitmap_state = BitmapState(num_columns, num_rows)
            
            # Map row IDs to sequential indices for bitmap
            row_id_to_index = {rid: idx for idx, rid in enumerate(rows_cols.keys())}
            index_to_row_id = {idx: rid for rid, idx in row_id_to_index.items()}
            
            # Set up row-column relationships in bitmap
            for rid, colset in rows_cols.items():
                row_idx = row_id_to_index[rid]
                col_indices = [cid for cid in colset if cid < num_columns]
                bitmap_state.set_row_columns(row_idx, col_indices)
            
            solution_rows: List[int] = []
            piece_usage: Dict[str, int] = {pid: 0 for pid in target_pieces}
            
            # Bitmap-based cover/uncover operations
            cover_stack: List[Tuple[int, int]] = []  # Stack of (removed_cols, removed_rows) bitmaps
            
            # Core Algorithm X search with bitmap optimization
            def search() -> Iterator[List[int]]:
                nonlocal results
                
                # Time check during recursive search
                if time_limit_seconds and (time.time() - start_time) >= time_limit_seconds:
                    raise StopIteration("Time limit reached")
                
                if bitmap_state.is_solved():
                    # print(f"DLX DEBUG: Found solution with {len(solution_rows)} pieces")
                    yield list(solution_rows)
                    return  # Continue searching for more solutions
                
                # Check for empty columns (unsolvable state)
                if bitmap_state.has_empty_column():
                    return
                
                # Choose column with minimum candidates (MRV heuristic)
                col, candidate_count = bitmap_state.choose_best_column()
                if col == -1 or candidate_count == 0:
                    return
                
                # Get candidates for this column
                candidate_indices = bitmap_state.get_column_candidates(col)
                candidate_row_ids = [index_to_row_id[idx] for idx in candidate_indices]
                candidate_row_ids = tie_shuffle(candidate_row_ids, rnd.randint(0, 2**31-1))
                
                for row_id in candidate_row_ids:
                    piece_id = rows_meta[row_id]["piece"]
                    if piece_usage[piece_id] >= target_inventory.get(piece_id, 0):
                        continue
                    
                    solution_rows.append(row_id)
                    piece_usage[piece_id] += 1
                    
                    # Cover the row using bitmap operations
                    row_idx = row_id_to_index[row_id]
                    removed_cols, removed_rows = bitmap_state.cover_row(row_idx)
                    cover_stack.append((removed_cols, removed_rows))
                    
                    for sol in search():
                        if isinstance(sol, dict) and sol.get("type") == "tick":
                            yield sol
                        else:
                            yield sol
                    
                    # Uncover using bitmap operations
                    removed_cols, removed_rows = cover_stack.pop()
                    bitmap_state.uncover(removed_cols, removed_rows)
                    piece_usage[piece_id] -= 1
                    solution_rows.pop()
            
            # Try Algorithm X search for this combination
            canonical_sigs = set()
            combination_found_solution = False
            
            # print(f"DLX DEBUG: Starting Algorithm X search with {num_columns} columns, {num_rows} rows")
            
            for sol_rows in search():
                if isinstance(sol_rows, dict) and sol_rows.get("type") == "tick":
                    yield sol_rows
                    continue
                
                # Build placements from solution
                placements = []
                pieces_used = {}
                
                for row_id in sol_rows:
                    meta = rows_meta[row_id]
                    piece_id = meta["piece"]
                    pieces_used[piece_id] = pieces_used.get(piece_id, 0) + 1
                    
                    placements.append({
                        "piece": piece_id,
                        "orientation": meta["ori"],
                        "position": list(meta["t"]),
                        "coordinates": [list(coord) for coord in meta["covered"]]
                    })
                
                # Canonical deduplication - use simple hash of placement coordinates
                from ...coords.canonical import cid_sha256
                all_coords = []
                for placement in placements:
                    all_coords.extend([tuple(coord) for coord in placement["coordinates"]])
                sig = cid_sha256(all_coords)
                
                if sig in canonical_sigs:
                    continue
                canonical_sigs.add(sig)
                
                print(f"DLX DEBUG: Emitting solution with {len(placements)} placements")
                yield {
                    "type": "solution",
                    "solution": {
                        "placements": placements,
                        "piecesUsed": pieces_used,
                        "canonical_signature": sig
                    }
                }
                
                combination_found_solution = True
                # Don't break here - continue searching for more solutions within this combination
            
            # Continue searching through all combinations until time limit reached
            # Don't break early - let time limit control termination
        
        # Emit done event
        yield {
            "type": "done",
            "metrics": {
                "nodes": 0,
                "pruned": 0,
                "depth": 0,
                "bestDepth": 0,
                "solutions": results
            }
        }
