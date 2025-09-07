from __future__ import annotations
from typing import Iterator, Dict, List, Tuple, Set, Any
import time, random
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...solver.symbreak import container_symmetry_group
from ...solver.heuristics import tie_shuffle
from ...io.solution_sig import canonical_state_signature

I3 = Tuple[int,int,int]

class DLXEngine(EngineProtocol):
    name = "dlx"
    
    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        """
        Algorithm X (exact cover) prototype over:
          - Columns: each container cell (cover exactly once)
                     + one column per piece *instance* (use at most count -> exact cover by duplicating a piece column per allowed instance)
          - Rows: each feasible placement (piece, orientation, translation), linking the cell columns it covers
                 and exactly one of the piece-instance columns for that piece.
        Small containers only; row build is O(#cells * #orients * #pieces).
        """
        t0 = time.time()
        seed = int(options.get("seed", 0))
        rnd = random.Random(seed)
        max_results = int(options.get("max_results", 1))

        cells_sorted: List[I3] = sorted(tuple(map(int,c)) for c in container["coordinates"])
        container_set = set(cells_sorted)
        symGroup = container_symmetry_group(cells_sorted)
        smallMode = (len(cells_sorted) <= 32)

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

        # --- Generate feasible placement rows ---
        # For DLX we need *all* placements upfront. Anchor convention:
        # use the FIRST atom of each orientation as anchor against every container cell.
        lib = load_fcc_A_to_Y()
        rows_cols: Dict[str, Set[str]] = {}   # row_id -> set(columns)
        rows_meta: Dict[str, Dict[str,Any]] = {}  # placement metadata to reconstruct solutions

        # Helper: test placement coverage & map to columns
        def placement_row_columns(covered: Tuple[I3,...], pid: str) -> List[Set[str]]:
            # cell columns
            try:
                cellset = { f"CELL:{cell_index[c]}" for c in covered }
            except KeyError:
                return []
            if any(c not in container_set for c in covered):
                return []
            # piece instance columns: duplicate row for each available slot of that pid
            slots = piece_slots.get(pid, [])
            if not slots:
                return []  # cannot place if no inventory slot
            return [ set([slot]) | set(cellset) for slot in slots ]

        # Build placements
        for pid, pdef in lib.items():
            if inv.get(pid,0) <= 0:
                continue
            for oi, orient in enumerate(pdef.orientations):
                if not orient: continue
                anchor = orient[0]
                # translate anchor to each container cell
                for c in cells_sorted:
                    dx,dy,dz = c[0]-anchor[0], c[1]-anchor[1], c[2]-anchor[2]
                    cov = tuple(sorted((u[0]+dx, u[1]+dy, u[2]+dz) for u in orient))
                    # check inside container & map to row columns (duplicated per piece slot)
                    row_col_sets = placement_row_columns(cov, pid)
                    if not row_col_sets:
                        continue
                    # emit a row for each piece slot
                    for colset in row_col_sets:
                        rid = f"{pid}|o{oi}|t{dx},{dy},{dz}|slot:{list(colset)[0]}"
                        rows_cols[rid] = colset
                        rows_meta[rid] = {"piece": pid, "ori": oi, "t": (dx,dy,dz), "covered": cov}

        # Order rows deterministically with seed
        row_ids = list(rows_cols.keys())
        row_ids = tie_shuffle(row_ids, seed)

        # --- Algorithm X (exact cover) ---
        # columns map -> rows containing it
        col_rows: Dict[str, Set[str]] = {col:set() for col in columns}
        for rid, colset in rows_cols.items():
            for col in colset:
                col_rows[col].add(rid)

        # choose column with min rows (MRV on columns)
        def choose_col(active_cols: Set[str]) -> str | None:
            # prefer cell columns first; then piece columns
            best = None; best_len = 10**9
            for col in active_cols:
                ln = len(col_rows[col] & active_rows)
                if ln < best_len:
                    best_len = ln; best = col
                    if best_len <= 1: break
            return best

        # Backtracking sets
        active_cols: Set[str] = set(columns)
        active_rows: Set[str] = set(row_ids)
        solution_rows: List[str] = []
        results = 0

        # Cover/uncover helpers
        def cover(col: str, removed_cols: List[str], removed_rows: List[str]):
            # remove col from active_cols
            if col not in active_cols: return
            active_cols.remove(col); removed_cols.append(col)
            # remove all rows that use col
            rs = list(col_rows[col] & active_rows)
            for r in rs:
                if r in active_rows:
                    active_rows.remove(r); removed_rows.append(r)
                    # remove other columns that row covered (for counting)
                    # (we don't mutate col_rows here; consult active_rows during choose)
            return

        def uncover(removed_cols: List[str], removed_rows: List[str]):
            # restore rows then columns (reverse order)
            while removed_rows:
                r = removed_rows.pop()
                active_rows.add(r)
            while removed_cols:
                c = removed_cols.pop()
                active_cols.add(c)

        # Core search
        def search() -> Iterator[List[str]]:
            nonlocal results
            # success: all cell columns are covered
            # i.e., none of CELL:* remain active
            if all(not col.startswith("CELL:") for col in active_cols):
                yield list(solution_rows)
                return
            col = choose_col(active_cols)
            if col is None:
                return
            # iterate rows that include chosen col
            # create a list snapshot to avoid mutation issues
            candidates = [r for r in (col_rows[col] & active_rows)]
            # deterministic shuffle under seed
            candidates = tie_shuffle(candidates, seed)
            for r in candidates:
                # choose row r
                solution_rows.append(r)
                # cover all columns used by r
                removed_cols: List[str] = []
                removed_rows: List[str] = []
                for c in rows_cols[r]:
                    cover(c, removed_cols, removed_rows)
                # remove all rows that conflict (share any of those columns)
                # conflict rows already removed via active_rows intersection filtering
                # recurse
                yield from search()
                # backtrack
                solution_rows.pop()
                uncover(removed_cols, removed_rows)

        # Emit solutions as they are found
        # The canonical dedup is enforced by the CLI write path (or we can include process-local set if desired)
        for rows in search():
            # reconstruct placements and canonical SID
            used_cells: Set[I3] = set()
            placements: List[Dict[str,Any]] = []
            used_slots: Set[str] = set()
            for rid in rows:
                meta = rows_meta[rid]
                # skip duplicate piece-slot rows (shouldn't happen if exact cover works)
                placements.append({"piece": meta["piece"], "ori": meta["ori"], "t": list(meta["t"]), "coordinates": [list(coord) for coord in meta["covered"]]})
                used_cells.update(meta["covered"])
                # track slot by id suffix (optional)
            sid_canon = canonical_state_signature(used_cells, symGroup)
            sol = {
                "containerCidSha256": container.get("cid_sha256", ""),
                "lattice": "fcc",
                "piecesUsed": inv,
                "placements": placements,
                "sid_state_sha256": "dlx_state",
                "sid_route_sha256": "dlx_route",
                "sid_state_canon_sha256": sid_canon,
            }
            yield {"t_ms": int((time.time()-t0)*1000), "type":"solution", "solution": sol}
            results += 1
            if results >= max_results:
                break

        # Always emit done
        yield {"t_ms": int((time.time()-t0)*1000), "type":"done",
               "metrics":{"solutions": results, "nodes": 0, "pruned": 0,
                          "bestDepth": 0, "smallMode": smallMode,
                          "symGroup": len(symGroup), "seed": seed}}
