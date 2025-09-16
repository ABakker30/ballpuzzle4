"""DLX Engine with piece combination iteration for exact cover solving.
Drop-in compatible with DFS engine event/status schemas.
"""

import time
import random
from typing import Iterator, Dict, List, Set, Any, Tuple, Optional

from ..engine_api import EngineProtocol  # and the runtime expects solve(...) to yield events
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...pieces.sphere_orientations import get_piece_orientations
from ...coords.symmetry_fcc import canonical_atom_tuple
from ...solver.heuristics import tie_shuffle

from ...common.status_snapshot import (
    StatusV2, PlacedPiece, ContainerInfo, Metrics, now_ms, label_for_piece, expand_piece_to_cells
)
from ...common.status_emitter import StatusEmitter

from ...io.solution_sig import canonical_state_signature
from ...solver.symbreak import container_symmetry_group

from .coordinate_mapper import CoordinateMapper
from .bitmap_state import BitmapState

I3 = Tuple[int, int, int]


class DLXEngine(EngineProtocol):
    name = "dlx"

    def solve(self, container, inventory, pieces, options) -> Iterator[Dict[str, Any]]:
        """Solve using Algorithm X with Dancing Links, iterating through piece combinations."""
        # -------------------------
        # Options (aligned with DFS)
        # -------------------------
        seed = int(options.get("seed", 42))
        max_rows_cap = options.get("max_rows_cap")  # optional global cap on candidate rows
        time_limit = float(options.get("time_limit", 0))  # 0/<=0 = no limit
        max_results = int(options.get("max_results", 1))

        # Status options (use StatusV2 like DFS)
        status_json = options.get("status_json")
        status_interval_ms = int(options.get("status_interval_ms", 1000))
        status_max_stack = int(options.get("status_max_stack", 512))
        status_phase = options.get("status_phase")

        # -------------------------
        # Run bookkeeping
        # -------------------------
        t0 = time.time()
        start_time_ms = now_ms()
        run_id = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
        rnd = random.Random(seed)

        # Container normalization (compatible with DFS)
        if isinstance(container, dict) and "coordinates" in container:
            container_coords: List[I3] = [tuple(map(int, c)) for c in container["coordinates"]]
            container_cid = container.get("cid_sha256", f"container_{hash(str(container))}")
        elif isinstance(container, (list, tuple)):
            container_coords = [tuple(map(int, c)) for c in container]
            container_cid = f"container_{hash(str(container_coords))}"
        else:
            container_coords = []
            container_cid = "container_empty"

        container_cells = sorted(container_coords)
        container_set = set(container_cells)
        container_size = len(container_cells)
        sym_group = container_symmetry_group(container_cells)

        # Inventory normalization
        inv: Dict[str, int] = inventory.get("pieces", {}) or inventory

        # Shared metrics (aligned keys with DFS)
        solutions_found = 0
        nodes_explored = 0
        max_depth_reached = 0
        max_pieces_placed = 0

        # For StatusV2 snapshots (approximate view like DFS)
        current_stack_rows: List[Dict[str, Any]] = []  # list of rows_meta entries for current partial solution

        # Piece index mapping for snapshot labels
        pieces_dict = load_fcc_A_to_Y()
        piece_names_sorted = sorted(pieces_dict.keys())
        piece_name_to_idx = {name: idx for idx, name in enumerate(piece_names_sorted)}

        # -------------------------
        # Status emitter (StatusV2)
        # -------------------------
        def build_snapshot() -> StatusV2:
            try:
                placed: List[PlacedPiece] = []
                instance_id = 1
                for meta in current_stack_rows[-status_max_stack:]:
                    # mirror DFS snapshot style: use piece_type label, expand from anchor
                    piece_name = meta.get("piece", "A")
                    piece_type = piece_name_to_idx.get(piece_name, 0)
                    piece_label = label_for_piece(piece_type)
                    covered = meta.get("covered") or []
                    anchor = covered[0] if covered else (0, 0, 0)
                    cells = expand_piece_to_cells(piece_type, anchor[0], anchor[1], anchor[2])
                    placed.append(PlacedPiece(
                        instance_id=instance_id,
                        piece_type=piece_type,
                        piece_label=piece_label,
                        cells=cells
                    ))
                    instance_id += 1

                elapsed = now_ms() - start_time_ms
                metrics = Metrics(
                    nodes=int(nodes_explored),
                    pruned=0,
                    depth=int(len(current_stack_rows)),
                    solutions=int(solutions_found),
                    elapsed_ms=int(elapsed),
                    best_depth=int(max_depth_reached) if max_depth_reached > 0 else None
                )
                return StatusV2(
                    version=2,
                    ts_ms=now_ms(),
                    engine="dlx",
                    phase=status_phase or "search",
                    run_id=run_id,
                    container=ContainerInfo(cid=container_cid, cells=container_size),
                    metrics=metrics,
                    stack=placed,
                    stack_truncated=len(current_stack_rows) > status_max_stack
                )
            except Exception:
                # Fallback on error
                return StatusV2(
                    version=2,
                    ts_ms=now_ms(),
                    engine="dlx",
                    phase=status_phase or "search",
                    run_id=run_id,
                    container=ContainerInfo(cid=container_cid, cells=container_size),
                    metrics=Metrics(nodes=0, pruned=0, depth=0, solutions=int(solutions_found), elapsed_ms=int(now_ms() - start_time_ms)),
                    stack=[],
                    stack_truncated=False
                )

        status_emitter: Optional[StatusEmitter] = None
        if status_json:
            try:
                status_emitter = StatusEmitter(status_json, status_interval_ms)
                status_emitter.start(build_snapshot)
            except Exception:
                status_emitter = None  # fail-open

        # -------------------------
        # Helpers
        # -------------------------
        def time_up() -> bool:
            return time_limit > 0 and (time.time() - t0) >= time_limit

        # Generate all valid piece-combinations that sum to container size
        def generate_piece_combinations(csize: int, available_pieces: Dict[str, int]) -> List[Dict[str, int]]:
            pieces_needed = csize // 4
            if csize % 4 != 0:
                return []

            total_available = sum(available_pieces.values())
            all_ones = all(count == 1 for count in available_pieces.values())

            # If inventory matches exact count and all are 1, use everything once
            if pieces_needed == total_available and all_ones:
                return [available_pieces.copy()]

            from itertools import combinations_with_replacement
            types = list(available_pieces.keys())
            combos: List[Dict[str, int]] = []
            for combo in combinations_with_replacement(types, pieces_needed):
                pc: Dict[str, int] = {}
                for p in combo:
                    pc[p] = pc.get(p, 0) + 1
                # within available limits?
                valid = True
                for p, cnt in pc.items():
                    if cnt > available_pieces.get(p, 0):
                        valid = False
                        break
                if valid:
                    combos.append(pc)
            return combos

        valid_combinations = generate_piece_combinations(container_size, inv)

        # Optional prioritization like your prior code
        working_combos = [
            {'A': 2, 'E': 1, 'T': 1},
            {'A': 2, 'E': 1, 'Y': 1},
            {'A': 1, 'E': 1, 'T': 2},
            {'E': 2, 'T': 2},
        ]
        prioritized = []
        for wc in working_combos:
            if wc in valid_combinations:
                valid_combinations.remove(wc)
                prioritized.append(wc)
        valid_combinations = prioritized + valid_combinations

        if not valid_combinations:
            if status_emitter:
                status_emitter.stop()
            yield {
                "type": "done",
                "metrics": {
                    "solutions_found": 0,
                    "nodes_explored": 0,
                    "time_elapsed": time.time() - t0,
                    "max_depth_reached": 0,
                    "max_pieces_placed": 0
                }
            }
            return

        # Coordinate mapper for row/column integer ids
        mapper = CoordinateMapper()
        container_coord_ids = mapper.map_coordinates(container_cells)  # expected 0..N-1 mapping

        # -------------------------
        # Main combination loop
        # -------------------------
        for combo_idx, target_inventory in enumerate(valid_combinations):
            if time_up() or solutions_found >= max_results:
                break

            # -------------------------
            # Candidate generation (bounded)
            # -------------------------
            rows_cols: Dict[int, Set[int]] = {}
            rows_meta: Dict[int, Dict[str, Any]] = {}
            seen_canon: Set[Tuple[str, Tuple[I3, ...]]] = set()
            best_per_cellset: Dict[frozenset, int] = {}  # cellset -> row_id

            # Budget
            CANDIDATE_BUDGET = 5000
            if max_rows_cap:
                try:
                    CANDIDATE_BUDGET = min(CANDIDATE_BUDGET, int(max_rows_cap))
                except Exception:
                    pass
            candidates_generated = 0
            early_exit = False

            # Piece prioritization: fewest orientations first
            priorities = []
            for pid in target_inventory.keys():
                try:
                    oris = get_piece_orientations(pid)
                    oc = len([o for o in oris if o])
                except Exception:
                    oc = 1
                priorities.append((oc, pid))
            priorities.sort()
            prioritized_pieces = [pid for _, pid in priorities]

            # Position priority: corners/edges first (simple boundary count)
            xs = [c[0] for c in container_cells]
            ys = [c[1] for c in container_cells]
            zs = [c[2] for c in container_cells]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            z_min, z_max = min(zs), max(zs)

            def pos_priority(coord: I3) -> int:
                x, y, z = coord
                boundary = 0
                if x in (x_min, x_max):
                    boundary += 1
                if y in (y_min, y_max):
                    boundary += 1
                if z in (z_min, z_max):
                    boundary += 1
                return -boundary  # corners (3) first

            prioritized_positions = sorted(container_cells, key=pos_priority)

            # Build candidate rows
            for pid in prioritized_pieces:
                if early_exit or time_up() or candidates_generated >= CANDIDATE_BUDGET:
                    break
                if target_inventory.get(pid, 0) <= 0:
                    continue

                try:
                    orientations = get_piece_orientations(pid)
                except KeyError:
                    orientations = [[[0, 0, 0]]]

                for oi, orient in enumerate(orientations):
                    if early_exit or time_up() or candidates_generated >= CANDIDATE_BUDGET:
                        break
                    if not orient:
                        continue
                    anchor = tuple(map(int, orient[0]))

                    for c in prioritized_positions:
                        if early_exit or time_up() or candidates_generated >= CANDIDATE_BUDGET:
                            break

                        dx, dy, dz = c[0] - anchor[0], c[1] - anchor[1], c[2] - anchor[2]
                        cov = tuple(sorted((u[0] + dx, u[1] + dy, u[2] + dz) for u in orient))
                        if any(cc not in container_set for cc in cov):
                            continue

                        canon = canonical_atom_tuple(cov)  # dedup same footprint per piece/orientation
                        key = (pid, canon)
                        if key in seen_canon:
                            continue
                        seen_canon.add(key)

                        # Map coordinates to integer ids
                        try:
                            coord_ids = mapper.map_coordinates(list(cov))
                            cellset = frozenset(coord_ids)
                        except KeyError:
                            continue

                        row_key = f"{pid}|o{oi}|t{dx},{dy},{dz}"
                        row_id = mapper.map_row(row_key, pid, oi, (dx, dy, dz), list(cov))

                        best_per_cellset[cellset] = row_id  # keep last (simple policy)
                        candidates_generated += 1
                        if max_rows_cap and candidates_generated >= int(max_rows_cap):
                            early_exit = True
                            break

            if time_up():
                break

            if not best_per_cellset:
                # No placements for this combo; move on
                continue

            # Finalize rows/cols
            for cellset, rid in best_per_cellset.items():
                rows_cols[rid] = cellset
                placement_info = mapper.get_placement_info(rid)
                rows_meta[rid] = {
                    "piece": placement_info["piece_id"],
                    "ori": placement_info["orientation_idx"],
                    "t": placement_info["position"],
                    "covered": [tuple(map(int, c)) for c in placement_info["coordinates"]],
                }

            # -------------------------
            # Build bitmap state for Algorithm X
            # -------------------------
            num_columns = len(container_cells)
            num_rows = len(rows_cols)

            bitmap_state = BitmapState(num_columns, num_rows)

            # stable index mapping for rows
            row_id_to_index = {rid: idx for idx, rid in enumerate(rows_cols.keys())}
            index_to_row_id = {idx: rid for rid, idx in row_id_to_index.items()}

            for rid, colset in rows_cols.items():
                row_idx = row_id_to_index[rid]
                col_indices = [cid for cid in colset if 0 <= cid < num_columns]
                bitmap_state.set_row_columns(row_idx, col_indices)

            solution_rows: List[int] = []
            piece_usage: Dict[str, int] = {p: 0 for p in target_inventory.keys()}
            cover_stack: List[Tuple[int, int]] = []  # (removed_cols_bitmap, removed_rows_bitmap)

            # -------------------------
            # DLX recursive search
            # -------------------------
            def search() -> Iterator[List[int]]:
                nonlocal nodes_explored, max_depth_reached, max_pieces_placed, current_stack_rows

                # update status bookkeeping
                nodes_explored += 1
                max_depth_reached = max(max_depth_reached, len(solution_rows))
                max_pieces_placed = max(max_pieces_placed, len(solution_rows))

                # refresh snapshot stack (like DFS)
                current_stack_rows = []
                for row_id in solution_rows[-status_max_stack:]:
                    if row_id in rows_meta:
                        current_stack_rows.append(rows_meta[row_id])

                # time check
                if time_up():
                    return

                if bitmap_state.is_solved():
                    yield list(solution_rows)
                    return

                if bitmap_state.has_empty_column():
                    return

                # MRV column (bitmap_state chooses col with min candidates)
                col, candidate_count = bitmap_state.choose_best_column()
                if col == -1 or candidate_count == 0:
                    return

                candidate_indices = bitmap_state.get_column_candidates(col)
                candidate_row_ids = [index_to_row_id[idx] for idx in candidate_indices]
                candidate_row_ids = tie_shuffle(candidate_row_ids, rnd.randint(0, 2**31 - 1))

                for row_id in candidate_row_ids:
                    piece_id = rows_meta[row_id]["piece"]
                    if piece_usage[piece_id] >= target_inventory.get(piece_id, 0):
                        continue

                    solution_rows.append(row_id)
                    piece_usage[piece_id] += 1

                    row_idx = row_id_to_index[row_id]
                    removed_cols, removed_rows = bitmap_state.cover_row(row_idx)
                    cover_stack.append((removed_cols, removed_rows))

                    for sol in search():
                        yield sol
                        if time_up():
                            break

                    # backtrack
                    removed_cols, removed_rows = cover_stack.pop()
                    bitmap_state.uncover(removed_cols, removed_rows)
                    piece_usage[piece_id] -= 1
                    solution_rows.pop()

                    if time_up():
                        return

            # -------------------------
            # Enumerate solutions for this combination
            # -------------------------
            for sol_rows in search():
                if time_up():
                    break

                # Build DFS-compatible solution event
                placements = []
                pieces_used: Dict[str, int] = {}
                all_coords: List[I3] = []

                for row_id in sol_rows:
                    meta = rows_meta[row_id]
                    piece_id = meta["piece"]
                    ori_idx = meta["ori"]
                    tvec = meta["t"]
                    covered = meta["covered"]

                    pieces_used[piece_id] = pieces_used.get(piece_id, 0) + 1
                    placements.append({
                        "piece": piece_id,
                        "ori": int(ori_idx),
                        "t": list(map(int, tvec)),
                        "cells_ijk": [list(map(int, c)) for c in covered]
                    })
                    all_coords.extend(covered)

                sid = canonical_state_signature(all_coords, sym_group)

                yield {
                    "type": "solution",
                    "t_ms": int((time.time() - t0) * 1000),
                    "solution": {
                        "containerCidSha256": container_cid,
                        "lattice": "fcc",
                        "piecesUsed": pieces_used,
                        "placements": placements,
                        "sid_state_sha256": "dlx_state",
                        "sid_route_sha256": "dlx_route",
                        "sid_state_canon_sha256": sid
                    }
                }

                solutions_found += 1
                if solutions_found >= max_results:
                    break

            if time_up() or solutions_found >= max_results:
                break

        # -------------------------
        # Finalize
        # -------------------------
        if status_emitter:
            try:
                status_emitter.stop()
            except Exception:
                pass

        yield {
            "type": "done",
            "metrics": {
                "solutions_found": solutions_found,
                "nodes_explored": nodes_explored,
                "time_elapsed": time.time() - t0,
                "max_depth_reached": max_depth_reached,
                "max_pieces_placed": max_pieces_placed
            }
        }
