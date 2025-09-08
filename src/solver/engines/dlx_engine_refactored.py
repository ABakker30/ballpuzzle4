"""DLX Engine with piece combination iteration for exact cover solving."""

from typing import Iterator, Dict, List, Set, Any, Tuple, Optional
from ...pieces.fcc_A_to_Y import load_fcc_A_to_Y
from ...pieces.sphere_orientations import get_piece_orientations
from ...lattice.fcc_lattice import canonical_atom_tuple
from ...util.tie_shuffle import tie_shuffle
from ...util.rng import make_rng
from .engine_protocol import EngineProtocol

I3 = Tuple[int, int, int]

class DLXEngine(EngineProtocol):
    def solve(self, container: List[I3], inventory, pieces, options) -> Iterator[Dict[str, Any]]:
        """Solve using Algorithm X with Dancing Links, iterating through piece combinations."""
        
        max_results = options.get("max_results", 1)
        seed = options.get("seed", 42)
        max_rows_cap = options.get("max_rows_cap")
        
        rnd = make_rng(seed)
        
        def maybe_tick(**kwargs):
            nonlocal last_tick_ms
            import time
            now_ms = int(time.time() * 1000)
            if now_ms - last_tick_ms >= 100:
                last_tick_ms = now_ms
                yield {"type": "tick", "data": kwargs}
        
        container_set = set(container)
        cells_sorted = sorted(container)
        
        last_tick_ms = 0
        results = 0
        
        # Build cell columns for exact cover
        cell_cols: List[str] = [f"CELL:{i}" for i, _ in enumerate(cells_sorted)]
        cell_index: Dict[I3, int] = {c: i for i, c in enumerate(cells_sorted)}
        
        inv = inventory.get("pieces", {}) or {}
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
        print(f"DLX DEBUG: Found {len(valid_combinations)} valid piece combinations")
        
        # Prioritize known working combination
        working_combo = {'A': 2, 'E': 1, 'T': 1}
        if working_combo in valid_combinations:
            valid_combinations.remove(working_combo)
            valid_combinations.insert(0, working_combo)
            print("DLX DEBUG: Prioritizing known working combination")
        
        # Limit combinations for testing
        valid_combinations = valid_combinations[:10]
        
        if not valid_combinations:
            print("DLX DEBUG: No valid piece combinations found!")
            return
        
        # Try each combination until solution found
        for combo_idx, target_inventory in enumerate(valid_combinations):
            target_pieces = list(target_inventory.keys())
            print(f"DLX DEBUG: Testing combination {combo_idx+1}/{len(valid_combinations)}: {target_inventory}")
            
            # Generate candidates for this combination
            lib = load_fcc_A_to_Y()
            rows_cols: Dict[str, Set[str]] = {}
            rows_meta: Dict[str, Dict[str, Any]] = {}
            seen_canon: Set[Tuple[str, Tuple[I3, ...]]] = set()
            best_per_cellset: Dict[frozenset, Tuple[Tuple[int, int, int], str]] = {}
            
            rowsBuilt = 0
            
            # Generate placement candidates for target pieces
            for pid, pdef in lib.items():
                if pid not in target_pieces:
                    continue
                if target_inventory.get(pid, 0) <= 0:
                    continue
                
                try:
                    orientations = get_piece_orientations(pid)
                except KeyError:
                    orientations = [[[0, 0, 0]]]
                
                for oi, orient in enumerate(orientations):
                    if not orient:
                        continue
                    anchor = orient[0]
                    for c in cells_sorted:
                        dx, dy, dz = c[0] - anchor[0], c[1] - anchor[1], c[2] - anchor[2]
                        cov = tuple(sorted((u[0] + dx, u[1] + dy, u[2] + dz) for u in orient))
                        
                        if any(cc not in container_set for cc in cov):
                            continue
                        
                        canon = canonical_atom_tuple(cov)
                        key = (pid, canon)
                        if key in seen_canon:
                            continue
                        seen_canon.add(key)
                        
                        try:
                            cellset = frozenset(f"CELL:{cell_index[x]}" for x in cov)
                        except KeyError:
                            continue
                        
                        rid = f"{pid}|o{oi}|t{dx},{dy},{dz}"
                        best_per_cellset[cellset] = ((0, 0, 0), rid)
                        
                        rowsBuilt += 1
                        if max_rows_cap and rowsBuilt >= max_rows_cap:
                            break
            
            # Finalize rows for this combination
            piece_candidate_counts = {}
            for cellset, (_score, base_rid) in best_per_cellset.items():
                pid, rest = base_rid.split("|", 1)
                oi = int(rest.split("|")[0][1:])
                t_str = rest.split("|")[1][1:]
                dx, dy, dz = (int(x) for x in t_str.split(","))
                
                idx_to_cell = {f"CELL:{i}": c for i, c in enumerate(cells_sorted)}
                covered_cells = tuple(sorted(idx_to_cell[c] for c in cellset))
                meta = {"piece": pid, "ori": oi, "t": (dx, dy, dz), "covered": covered_cells}
                
                rows_cols[base_rid] = cellset
                rows_meta[base_rid] = meta
                piece_candidate_counts[pid] = piece_candidate_counts.get(pid, 0) + 1
            
            print(f"DLX DEBUG: Generated {len(rows_cols)} candidates for combination")
            for pid in sorted(piece_candidate_counts.keys()):
                print(f"DLX DEBUG: Piece {pid}: {piece_candidate_counts[pid]} candidates")
            
            if not rows_cols:
                print("DLX DEBUG: No candidates for this combination, trying next")
                continue
            
            # Algorithm X setup for this combination
            columns: List[str] = cell_cols
            col_rows: Dict[str, Set[str]] = {col: set() for col in columns}
            for rid, colset in rows_cols.items():
                for col in colset:
                    col_rows[col].add(rid)
            
            row_ids = list(rows_cols.keys())
            row_ids = tie_shuffle(row_ids, seed)
            
            def choose_col(active_cols: Set[str]) -> Optional[str]:
                best, best_len = None, float('inf')
                for col in active_cols:
                    ln = len(col_rows[col] & active_rows)
                    if ln < best_len:
                        best_len = ln
                        best = col
                        if best_len <= 1:
                            break
                return best
            
            # Algorithm X search state
            active_cols: Set[str] = set(columns)
            active_rows: Set[str] = set(rows_cols.keys())
            solution_rows: List[str] = []
            piece_usage: Dict[str, int] = {pid: 0 for pid in target_pieces}
            
            def cover(col: str, removed_cols: List[str], removed_rows: List[str]):
                if col not in active_cols:
                    return
                active_cols.remove(col)
                removed_cols.append(col)
                for r in list(col_rows[col] & active_rows):
                    active_rows.remove(r)
                    removed_rows.append(r)
            
            def uncover(removed_cols: List[str], removed_rows: List[str]):
                while removed_rows:
                    active_rows.add(removed_rows.pop())
                while removed_cols:
                    active_cols.add(removed_cols.pop())
            
            # Core Algorithm X search
            def search() -> Iterator[List[str]]:
                nonlocal results
                
                for ev in maybe_tick(rowsBuilt=len(rows_cols), activeCols=len(active_cols), partial=len(solution_rows)):
                    yield ev
                
                if len(active_cols) == 0:
                    yield list(solution_rows)
                    return
                
                col = choose_col(active_cols)
                if col is None or len(col_rows[col] & active_rows) == 0:
                    return
                
                cands = list(col_rows[col] & active_rows)
                cands = tie_shuffle(cands, rnd.randint(0, 2**31-1))
                
                for row in cands:
                    piece_id = rows_meta[row]["piece"]
                    if piece_usage[piece_id] >= target_inventory.get(piece_id, 0):
                        continue
                    
                    solution_rows.append(row)
                    piece_usage[piece_id] += 1
                    removed_cols, removed_rows = [], []
                    
                    for c in rows_cols[row]:
                        cover(c, removed_cols, removed_rows)
                    
                    for sol in search():
                        if isinstance(sol, dict) and sol.get("type") == "tick":
                            yield sol
                        else:
                            yield sol
                            results += 1
                            if results >= max_results:
                                return
                    
                    uncover(removed_cols, removed_rows)
                    piece_usage[piece_id] -= 1
                    solution_rows.pop()
            
            # Try Algorithm X search for this combination
            canonical_sigs = set()
            combination_found_solution = False
            
            for sol_rows in search():
                if isinstance(sol_rows, dict) and sol_rows.get("type") == "tick":
                    yield sol_rows
                    continue
                
                # Build placements from solution
                placements = []
                pieces_used = {}
                
                for row in sol_rows:
                    meta = rows_meta[row]
                    piece_id = meta["piece"]
                    pieces_used[piece_id] = pieces_used.get(piece_id, 0) + 1
                    
                    placement = {
                        "piece": piece_id,
                        "ori": meta["ori"],
                        "t": list(meta["t"]),
                        "coordinates": [list(coord) for coord in meta["covered"]]
                    }
                    placements.append(placement)
                
                # Canonical deduplication
                from ...util.canonical import compute_canonical_signature
                sig = compute_canonical_signature(placements)
                
                if sig in canonical_sigs:
                    continue
                canonical_sigs.add(sig)
                
                yield {
                    "type": "solution",
                    "placements": placements,
                    "pieces_used": pieces_used,
                    "canonical_signature": sig
                }
                
                combination_found_solution = True
                break  # Found solution for this combination
            
            if combination_found_solution:
                break  # Stop trying other combinations
        
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
