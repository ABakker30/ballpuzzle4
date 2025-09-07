from __future__ import annotations
from typing import Iterator, Dict, List, Tuple, Set, Any
import time, random
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...solver.symbreak import container_symmetry_group
from ...solver.heuristics import tie_shuffle
from ...io.solution_sig import canonical_state_signature
from ...coords.symmetry_fcc import canonical_atom_tuple

I3 = Tuple[int,int,int]

class DLXEngine(EngineProtocol):
    name = "dlx"
    
    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        """
        Algorithm X (exact cover) with scaling optimizations:
          - Symmetry-aware row reduction using canonical_atom_tuple
          - Simple dominance pruning for identical cell coverage
          - Configurable row caps with clean termination
          - Progress tick events with DLX-specific metrics
        """
        t0 = time.time()
        seed = int(options.get("seed", 0))
        rnd = random.Random(seed)
        max_results = int(options.get("max_results", 1))
        progress_every = int(options.get("progress_interval_ms", 0))
        caps = options.get("caps", {}) or {}
        max_rows_cap = int(caps.get("maxRows", 0))

        cells_sorted: List[I3] = sorted(tuple(map(int,c)) for c in container["coordinates"])
        container_set = set(cells_sorted)
        symGroup = container_symmetry_group(cells_sorted)
        smallMode = (len(cells_sorted) <= 32)

        def maybe_tick(rowsBuilt: int = 0, activeCols: int = 0, partial: int = 0):
            nonlocal last_tick_ms
            if not progress_every: return
            now = int((time.time()-t0)*1000)
            if now - last_tick_ms >= progress_every:
                last_tick_ms = now
                yield {"t_ms": now, "type":"tick",
                       "metrics":{"rows": rowsBuilt, "activeCols": activeCols, "partial": partial,
                                  "nodes": 0, "pruned": 0, "depth": 0, "bestDepth": 0, "solutions": results}}

        last_tick_ms = 0
        results = 0

        # --- Build exact cover universe ---
        # Columns: cell columns + piece-slot columns
        cell_cols: List[str] = [f"CELL:{i}" for i,_ in enumerate(cells_sorted)]
        cell_index: Dict[I3,int] = {c:i for i,c in enumerate(cells_sorted)}

        # Piece slots (duplicate per inventory count)
        inv = inventory.get("pieces", {}) or {}
        piece_slots: Dict[str,List[str]] = {}
        piece_slot_cols: List[str] = []
        for pid, cnt in inv.items():
            if cnt <= 0: continue
            slots = [f"PIECE:{pid}:{k}" for k in range(cnt)]
            piece_slots[pid] = slots
            piece_slot_cols.extend(slots)

        columns: List[str] = cell_cols + piece_slot_cols

        # --- Generate feasible placement rows with optimizations ---
        lib = load_fcc_A_to_Y()
        rows_cols: Dict[str, Set[str]] = {}
        rows_meta: Dict[str, Dict[str,Any]] = {}

        # canonical key: (piece, canonical_atom_tuple(covered))
        seen_canon: Set[Tuple[str, Tuple[I3,...]]] = set()

        # temp map for dominance: key = frozenset(cell cols), value = (score, rid)
        best_per_cellset: Dict[frozenset, Tuple[Tuple[int,int,int], str]] = {}

        def dominance_score(pid: str, covered: Tuple[I3,...], oi: int) -> Tuple[int,int,int]:
            # lower is better: (piece availability asc, -covered_size, orientation idx)
            # covered_size equal for our 4-sphere pieces; keep form for generality
            return (inv.get(pid, 0), -len(covered), oi)

        rowsBuilt = 0
        for pid, pdef in lib.items():
            if inv.get(pid,0) <= 0:
                continue
            for oi, orient in enumerate(pdef.orientations):
                if not orient: continue
                anchor = orient[0]
                for c in cells_sorted:
                    dx,dy,dz = c[0]-anchor[0], c[1]-anchor[1], c[2]-anchor[2]
                    cov = tuple(sorted((u[0]+dx, u[1]+dy, u[2]+dz) for u in orient))
                    # inside container?
                    if any(cc not in container_set for cc in cov):
                        continue
                    # symmetry-aware reduction
                    canon = canonical_atom_tuple(cov)
                    key = (pid, canon)
                    if key in seen_canon:
                        continue
                    seen_canon.add(key)

                    # map to cell columns
                    try:
                        cellset = frozenset(f"CELL:{cell_index[x]}" for x in cov)
                    except KeyError:
                        continue

                    # dominance check per identical cellset
                    score = dominance_score(pid, cov, oi)
                    prev = best_per_cellset.get(cellset)
                    if prev is not None and prev[0] <= score:
                        # existing is better or equal; skip
                        continue
                    # else keep and (if replacing) drop old later
                    best_per_cellset[cellset] = (score, f"{pid}|o{oi}|t{dx},{dy},{dz}")

                    rowsBuilt += 1
                    if max_rows_cap and rowsBuilt >= max_rows_cap:
                        for ev in maybe_tick(rowsBuilt=rowsBuilt, activeCols=len(columns), partial=len(best_per_cellset)):
                            yield ev
                        break
                if max_rows_cap and rowsBuilt >= max_rows_cap:
                    break
            if max_rows_cap and rowsBuilt >= max_rows_cap:
                break

        # finalize rows (expand by piece-slots)
        for cellset, (_score, base_rid) in best_per_cellset.items():
            pid, rest = base_rid.split("|",1)
            slots = piece_slots.get(pid, [])
            if not slots:
                continue
            # reconstruct placement meta from base_rid
            # rest: o{oi}|t{dx,dy,dz}
            oi = int(rest.split("|")[0][1:])
            t_str = rest.split("|")[1][1:]
            dx,dy,dz = (int(x) for x in t_str.split(","))
            # Build reverse map
            idx_to_cell = {f"CELL:{i}": c for i,c in enumerate(cells_sorted)}
            covered_cells = tuple(sorted(idx_to_cell[c] for c in cellset))
            meta = {"piece": pid, "ori": oi, "t": (dx,dy,dz), "covered": covered_cells}

            for slot in slots:
                rid = f"{base_rid}|slot:{slot}"
                cols = set(cellset) | {slot}
                rows_cols[rid] = cols
                rows_meta[rid] = meta

        # Order rows deterministically with seed
        row_ids = list(rows_cols.keys())
        row_ids = tie_shuffle(row_ids, seed)

        # --- Algorithm X (exact cover) ---
        # columns map -> rows containing it
        col_rows: Dict[str, Set[str]] = {col:set() for col in columns}
        for rid, colset in rows_cols.items():
            for col in colset:
                col_rows[col].add(rid)

        # choose column with MRV; prioritize cell columns
        def choose_col(active_cols: Set[str]) -> str | None:
            best = None; best_len = 10**9
            # pass 1: CELL:
            for col in active_cols:
                if not col.startswith("CELL:"):
                    continue
                ln = len(col_rows[col] & active_rows)
                if ln < best_len:
                    best_len = ln; best = col
                    if best_len <= 1: break
            if best is not None:
                return best
            # pass 2: PIECE:
            for col in active_cols:
                ln = len(col_rows[col] & active_rows)
                if ln < best_len:
                    best_len = ln; best = col
                    if best_len <= 1: break
            return best

        # search sets
        active_cols: Set[str] = set(columns)
        active_rows: Set[str] = set(rows_cols.keys())
        solution_rows: List[str] = []

        # cover/uncover
        def cover(col: str, removed_cols: List[str], removed_rows: List[str]):
            if col not in active_cols: return
            active_cols.remove(col); removed_cols.append(col)
            for r in list(col_rows[col] & active_rows):
                active_rows.remove(r); removed_rows.append(r)

        def uncover(removed_cols: List[str], removed_rows: List[str]):
            while removed_rows:
                active_rows.add(removed_rows.pop())
            while removed_cols:
                active_cols.add(removed_cols.pop())

        # emit initial tick after build
        for ev in maybe_tick(rowsBuilt=len(rows_cols), activeCols=len(active_cols), partial=len(solution_rows)):
            yield ev

        # Core search with tick events
        def search() -> Iterator[List[str]]:
            nonlocal results
            # emit tick periodically
            for ev in maybe_tick(rowsBuilt=len(rows_cols), activeCols=len(active_cols), partial=len(solution_rows)):
                yield ev
            
            # success: all cell columns covered
            if all(not col.startswith("CELL:") for col in active_cols):
                yield list(solution_rows)
                return
            
            col = choose_col(active_cols)
            if col is None or len(col_rows[col] & active_rows) == 0:
                return  # no solution
            
            # try each row covering col
            cands = list(col_rows[col] & active_rows)
            cands = tie_shuffle(cands, rnd.randint(0, 2**31-1))
            for row in cands:
                solution_rows.append(row)
                removed_cols, removed_rows = [], []
                for c in rows_cols[row]:
                    cover(c, removed_cols, removed_rows)
                
                for sol in search():
                    if isinstance(sol, dict) and sol.get("type") == "tick":
                        yield sol  # pass through tick events
                    else:
                        yield sol
                        results += 1
                        if results >= max_results:
                            return
                
                uncover(removed_cols, removed_rows)
                solution_rows.pop()

        # Solve with canonical dedup
        canonical_sigs = set()
        for sol_rows in search():
            if isinstance(sol_rows, dict) and sol_rows.get("type") == "tick":
                yield sol_rows  # pass through tick events
                continue
                
            # build placements from solution
            placements = []
            for rid in sol_rows:
                meta = rows_meta[rid]
                # Include coordinates field to match DFS engine format
                covered_coords = [list(c) for c in meta["covered"]]
                placements.append({
                    "piece": meta["piece"], 
                    "ori": meta["ori"], 
                    "t": list(meta["t"]),
                    "coordinates": covered_coords
                })
            
            # canonical dedup
            sig = ""
            if smallMode:
                # Extract occupied cells from placements
                from ...io.solution_sig import extract_occupied_cells_from_placements
                occupied_cells = extract_occupied_cells_from_placements(placements)
                sig = canonical_state_signature(occupied_cells, symGroup)
                if sig in canonical_sigs:
                    continue
                canonical_sigs.add(sig)
            
            # emit solution
            solution_data = {
                "containerCidSha256": container.get("cid_sha256", ""),
                "lattice": "fcc",
                "placements": placements,
                "sid_state_canon_sha256": sig
            }
            yield {"type": "solution", "t_ms": int((time.time()-t0)*1000),
                   "solution": solution_data}
            if results >= max_results:
                break

        # Check for early termination due to row cap
        if max_rows_cap and len(rows_cols) == 0:
            # No rows built due to cap; emit done with no solutions
            yield {"type": "done", "t_ms": int((time.time()-t0)*1000),
                   "metrics": {"solutions": 0, "rowsBuilt": 0, "cappedByRows": True}}
            return

        # Final done event
        yield {"type": "done", "t_ms": int((time.time()-t0)*1000),
               "metrics": {"solutions": results, "rowsBuilt": len(rows_cols)}}
