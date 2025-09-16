"""Bitmask-optimized DFS engine for rhombohedral (FCC) integer lattice solving (R6 adjacency only).

Features preserved:
- Root-level timed/node restarts (pivot over start piece and orientation)
- MRV window target-cell heuristic
- Hole-pruning modes (none | single_component | lt4) with legacy --hole4 alias
- Status snapshots (compatible with existing UI)

Improvements:
- Correct support for multiple copies of the same piece type (PieceBag counts)
- Pure integer lattice end-to-end (no world coords)
- Final R6 connectivity gate before emitting a solution
- Optional debug assertions for integer-only IO and library connectivity

NOTE: R6 adjacency only (±1 in exactly one coordinate).
"""

import time
import random
from typing import Iterator, Dict, Any, List, Tuple, Optional

from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...solver.tt import SeenMasks
from ...solver.heuristics import tie_shuffle
from ...solver.placement_gen import Placement
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...pieces.inventory import PieceBag
from ...io.solution_sig import canonical_state_signature
from ...solver.symbreak import container_symmetry_group
# from .engine_c.lattice_fcc import FCC_NEIGHBORS   # <- NOT USED (legacy 12-neighbor). We use R6 below.
from .engine_c.bitset import popcount, bitset_from_indices
from ...common.status_snapshot import (
    ContainerInfo, StatusV2, PlacedPiece, Metrics, now_ms
)
from ...common.status_emitter import StatusEmitter

I3 = Tuple[int, int, int]

# -----------------------------
# Rhombohedral 6-neighbor set
# -----------------------------
R6_NEIGHBORS: List[I3] = [
    ( 1, 0, 0), (-1, 0, 0),
    ( 0, 1, 0), ( 0,-1, 0),
    ( 0, 0, 1), ( 0, 0,-1),
]


# --------------------------------
# Local signal for root-level restarts
# --------------------------------
class _RestartSignal(Exception):
    pass


# --------------------------------
# Integer-lattice state (R6)
# --------------------------------
class BitmaskDFSState:
    """Efficient bitmask-based state representation for DFS search (integer FCC lattice, R6 adjacency)."""

    def __init__(self, container_cells: List[I3]):
        self.container_cells = container_cells
        self.num_cells = len(container_cells)

        # IJK integer mapping
        self.cell_to_index = {cell: i for i, cell in enumerate(container_cells)}
        self.index_to_cell = {i: cell for i, cell in enumerate(container_cells)}

        # Precompute neighbor relationships as bitmasks (R6 only)
        self.neighbor_masks: Dict[int, int] = {}
        for i, cell in enumerate(container_cells):
            neighbors = []
            for dx, dy, dz in R6_NEIGHBORS:
                n = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                if n in self.cell_to_index:
                    neighbors.append(self.cell_to_index[n])
            self.neighbor_masks[i] = bitset_from_indices(neighbors, self.num_cells)

        # Occupancy
        self.occupied_mask: int = 0
        self.seen_masks = SeenMasks()

    def is_occupied(self, cell_index: int) -> bool:
        return bool(self.occupied_mask & (1 << cell_index))

    def place_piece(self, placement: Placement) -> int:
        """Place a piece and return the bitmask of newly occupied cells."""
        new_mask = 0
        for cell in placement.covered:
            idx = self.cell_to_index.get(cell)
            if idx is None:
                # outside container (should not happen if validity checked)
                return 0
            new_mask |= (1 << idx)
        self.occupied_mask |= new_mask
        return new_mask

    def remove_piece(self, piece_mask: int):
        self.occupied_mask &= ~piece_mask

    def get_empty_cells(self) -> List[int]:
        """Indices of currently empty cells."""
        empty = []
        for i in range(self.num_cells):
            if not (self.occupied_mask & (1 << i)):
                empty.append(i)
        return empty

    def get_empty_mask(self) -> int:
        return ((1 << self.num_cells) - 1) & (~self.occupied_mask)

    def count_empty_cells(self) -> int:
        return popcount(self.get_empty_mask())

    def get_first_empty_cell(self) -> Optional[I3]:
        empty_mask = self.get_empty_mask()
        if empty_mask == 0:
            return None
        for i in range(self.num_cells):
            if empty_mask & (1 << i):
                return self.index_to_cell[i]
        return None

    def _component_size_lt_k_r6(self, start_idx: int, k: int, empty_set: set) -> bool:
        """Return True if connected component size from start (R6) is < k."""
        visited = set()
        queue = [start_idx]
        size = 0
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            size += 1
            if size >= k:
                return False
            neigh_mask = self.neighbor_masks.get(cur, 0)
            nm = neigh_mask
            while nm:
                lsb = nm & -nm
                n_idx = (lsb.bit_length() - 1)
                if (n_idx in empty_set) and (n_idx not in visited):
                    queue.append(n_idx)
                nm &= ~lsb
        return True

    def has_holes_single_component(self) -> bool:
        """True if empty cells split into >1 connected components (R6 adjacency)."""
        empty = set(self.get_empty_cells())
        if len(empty) <= 1:
            return False
        start = next(iter(empty))
        visited = set()
        queue = [start]
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            neigh_mask = self.neighbor_masks.get(cur, 0)
            nm = neigh_mask
            while nm:
                lsb = nm & -nm
                n_idx = (lsb.bit_length() - 1)
                if (n_idx in empty) and (n_idx not in visited):
                    queue.append(n_idx)
                nm &= ~lsb
        return len(visited) < len(empty)

    def has_holes_lt4(self) -> bool:
        """True if any connected empty component has size < 4 (R6 adjacency)."""
        empty = set(self.get_empty_cells())
        if not empty:
            return False
        visited_global = set()
        for idx in list(empty):
            if idx in visited_global:
                continue
            local_visited = set()
            queue = [idx]
            size = 0
            while queue:
                cur = queue.pop(0)
                if cur in local_visited:
                    continue
                local_visited.add(cur)
                visited_global.add(cur)
                size += 1
                if size >= 4:
                    break
                neigh_mask = self.neighbor_masks.get(cur, 0)
                nm = neigh_mask
                while nm:
                    lsb = nm & -nm
                    n_idx = (lsb.bit_length() - 1)
                    if (n_idx in empty) and (n_idx not in local_visited):
                        queue.append(n_idx)
                    nm &= ~lsb
            if size < 4:
                return True
        return False

    def is_valid_placement(self, placement: Placement) -> bool:
        """Inside container and no collisions (integer FCC lattice, R6)."""
        for cell in placement.covered:
            idx = self.cell_to_index.get(cell)
            if idx is None or self.is_occupied(idx):
                return False
        return True


# --------------------------------
# Integer R6 connectivity (final safety gate)
# --------------------------------
def _connected_r6(cells_ijk: List[I3]) -> bool:
    if not cells_ijk:
        return True
    S = set(cells_ijk)
    from collections import deque
    q = deque([next(iter(S))])
    seen = set()
    while q:
        x, y, z = q.popleft()
        if (x, y, z) in seen:
            continue
        seen.add((x, y, z))
        for dx, dy, dz in R6_NEIGHBORS:
            n = (x + dx, y + dy, z + dz)
            if (n in S) and (n not in seen):
                q.append(n)
    return len(seen) == len(S)


# --------------------------------
# Engine
# --------------------------------
class DFSEngine(EngineProtocol):
    name = "dfs"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        t0 = time.time()
        start_time_ms = now_ms()

        # Options
        seed = int(options.get("seed", 0))
        random.seed(seed)
        time_limit = float(options.get("time_limit", float("inf")))
        max_results = int(options.get("max_results", 1))

        # Enhanced DFS knobs
        restart_interval_s = float(options.get("restart_interval_s", 30.0))
        restart_nodes = int(options.get("restart_nodes", 100_000))
        pivot_cycle = bool(options.get("pivot_cycle", True))
        mrv_window = int(options.get("mrv_window", 0))  # 0 = disabled
        hole_pruning = options.get("hole_pruning", "none")  # none | single_component | lt4
        if options.get("hole4", False):
            hole_pruning = "lt4"

        # Dev assertions (optional)
        assert_library = bool(options.get("assert_library", False))
        assert_io = bool(options.get("assert_io", False))

        # Status/snapshots
        status_json = options.get("status_json")
        status_interval_ms = options.get("status_interval_ms", 1000)
        status_max_stack = options.get("status_max_stack", 512)
        status_phase = options.get("status_phase")

        # Run metadata
        run_id = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())

        # --- Container (must be integer IJK) ---
        # Handle both "coordinates" and "cells" formats
        coords_raw = container.get("coordinates") or container.get("cells", [])
        if assert_io:
            for c in coords_raw:
                assert isinstance(c, (list, tuple)) and len(c) == 3, f"Bad cell: {c}"
                assert all(isinstance(v, int) for v in c), f"Non-integer container cell: {c}"
        container_cells = sorted(tuple(int(x) for x in c) for c in coords_raw)
        container_cells_count = len(container_cells)
        container_cid = container.get("cid_sha256", f"container_{hash(str(container))}")

        if container_cells_count % 4 != 0:
            yield {
                "type": "done",
                "metrics": {
                    "solutions_found": 0,
                    "nodes_explored": 0,
                    "time_elapsed": time.time() - t0,
                },
            }
            return

        # Pieces & inventory (counts per type)
        pieces_dict = load_fcc_A_to_Y()
        if assert_library:
            # Validate library orientations are integer-connected on R6
            for name, pdef in pieces_dict.items():
                for k, ori in enumerate(pdef.orientations):
                    assert all(isinstance(v, int) for cell in ori for v in cell), f"Non-int in {name}[{k}]"
                    if not _connected_r6(list(map(tuple, ori))):
                        raise AssertionError(f"Disconnected orientation {name}[{k}] under R6")

        piece_counts = inventory.get("pieces", inventory)
        piece_counts = {k: int(v) for k, v in piece_counts.items() if int(v) > 0}

        pieces_needed = container_cells_count // 4
        if sum(piece_counts.values()) < pieces_needed:
            yield {
                "type": "done",
                "metrics": {
                    "solutions_found": 0,
                    "nodes_explored": 0,
                    "time_elapsed": time.time() - t0,
                },
            }
            return

        # Search state
        state = BitmaskDFSState(container_cells)
        symGroup = container_symmetry_group(container_cells)

        solutions_found = 0
        nodes_explored = 0
        max_depth_reached = 0
        max_pieces_placed = 0
        current_placement_stack: List[Tuple[Placement, int]] = []
        restart_count = 0
        last_restart_time = time.time()
        last_restart_nodes = 0

        # Pivot across piece *types* and an orientation index
        all_piece_types = sorted(piece_counts.keys())
        pivot_pieces: List[Tuple[str, int]] = [(p, 0) for p in all_piece_types]
        pivot_idx = 0

        def advance_pivot():
            nonlocal pivot_idx
            if not pivot_cycle or not pivot_pieces:
                return
            pivot_idx = (pivot_idx + 1) % len(pivot_pieces)

        def current_pivot() -> Tuple[Optional[str], int]:
            if not pivot_pieces:
                return None, 0
            return pivot_pieces[pivot_idx]

        # Snapshot builder — uses the *actual placed cells* (no re-expansion)
        def build_snapshot() -> StatusV2:
            try:
                placed_list: List[PlacedPiece] = []
                instance_id = 1
                # Keep piece labeling for UI tags, but do not regenerate cell geometry
                piece_names_sorted = sorted(pieces_dict.keys())
                piece_name_to_idx = {n: i for i, n in enumerate(piece_names_sorted)}

                for pl, _mask in current_placement_stack:
                    ptype_idx = piece_name_to_idx.get(pl.piece, 0)
                    placed_list.append(
                        PlacedPiece(
                            instance_id=instance_id,
                            piece_type=ptype_idx,         # for label mapping only
                            piece_label=pl.piece,         # readable piece name
                            cells=list(pl.covered),       # integer IJK as placed
                        )
                    )
                    instance_id += 1

                truncated = False
                if len(placed_list) > status_max_stack:
                    placed_list = placed_list[-status_max_stack:]
                    truncated = True

                elapsed = now_ms() - start_time_ms
                metrics = Metrics(
                    nodes=int(nodes_explored),
                    pruned=0,
                    depth=int(len(current_placement_stack)),
                    solutions=int(solutions_found),
                    elapsed_ms=int(elapsed),
                    best_depth=int(max_depth_reached) if max_depth_reached > 0 else None,
                )
                return StatusV2(
                    version=2,
                    ts_ms=now_ms(),
                    engine="dfs",
                    phase=status_phase or "search",
                    run_id=run_id,
                    container=ContainerInfo(cid=container_cid, cells=container_cells_count),
                    metrics=metrics,
                    stack=placed_list,
                    stack_truncated=truncated,
                )
            except Exception:
                metrics = Metrics(nodes=0, pruned=0, depth=0, solutions=0, elapsed_ms=0)
                return StatusV2(
                    version=2,
                    ts_ms=now_ms(),
                    engine="dfs",
                    phase=status_phase or "search",
                    run_id=run_id,
                    container=ContainerInfo(cid=container_cid, cells=container_cells_count),
                    metrics=metrics,
                    stack=[],
                    stack_truncated=False,
                )

        status_emitter = None
        if status_json:
            try:
                status_emitter = StatusEmitter(status_json, status_interval_ms)
                status_emitter.start(build_snapshot)
            except Exception:
                status_emitter = None

        # Target selection (MRV over a window of empties; 0 -> first empty)
        def select_target_cell_mrv(st: BitmaskDFSState, window_size: int) -> Optional[I3]:
            empty_idxs = st.get_empty_cells()
            if not empty_idxs:
                return None
            if window_size <= 0 or window_size >= len(empty_idxs):
                return st.index_to_cell[empty_idxs[0]]

            # Choose the most constrained among a small window (fewest empty neighbors)
            best = None
            best_score = None
            for idx in empty_idxs[:window_size]:
                neigh_mask = st.neighbor_masks.get(idx, 0)
                # Count empty neighbors via bitset
                cnt = 0
                nm = neigh_mask
                while nm:
                    lsb = nm & -nm
                    n_idx = (lsb.bit_length() - 1)
                    if not st.is_occupied(n_idx):
                        cnt += 1
                    nm &= ~lsb
                if best_score is None or cnt < best_score:
                    best_score = cnt
                    best = idx
            return st.index_to_cell[best] if best is not None else st.get_first_empty_cell()

        def should_prune_holes(st: BitmaskDFSState, mode: str) -> bool:
            if mode == "none":
                return False
            if mode == "single_component":
                return st.has_holes_single_component()
            if mode == "lt4":
                return st.has_holes_lt4()
            return False

        # ---------------- Core DFS (R6) ----------------
        def dfs(depth: int, placement_stack: List[Tuple[Placement, int]], bag: PieceBag) -> Iterator[SolveEvent]:
            nonlocal solutions_found, nodes_explored, max_depth_reached, max_pieces_placed, current_placement_stack
            nonlocal last_restart_time, last_restart_nodes, restart_count

            # Time bound
            if time_limit > 0 and (time.time() - t0) >= time_limit:
                return

            # Restart policy from root only
            if depth == 0:
                now_t = time.time()
                if (now_t - last_restart_time) >= restart_interval_s or (nodes_explored - last_restart_nodes) >= restart_nodes:
                    raise _RestartSignal()

            nodes_explored += 1
            if depth > max_depth_reached:
                max_depth_reached = depth
            if len(placement_stack) > max_pieces_placed:
                max_pieces_placed = len(placement_stack)

            empty_count = state.count_empty_cells()
            if empty_count == 0:
                # SOLUTION — build output directly from placed data (integer-only)
                placements_list = [pl for pl, _m in placement_stack]

                # Final R6 connectivity gate (per-piece)
                for pl in placements_list:
                    if not _connected_r6(list(map(tuple, pl.covered))):
                        return  # reject and continue search

                # Metrics and signature
                solutions_found += 1
                solution_placements = []
                all_occupied_cells: List[I3] = []

                for pl in placements_list:
                    solution_placements.append({
                        "piece": pl.piece,
                        "ori": pl.ori_idx,
                        "t": list(pl.t),  # integer IJK translation
                        "cells_ijk": [list(c) for c in pl.covered],  # integer IJK cells
                    })
                    all_occupied_cells.extend(pl.covered)

                pieces_used: Dict[str, int] = {}
                for pl in placements_list:
                    pieces_used[pl.piece] = pieces_used.get(pl.piece, 0) + 1

                sid = canonical_state_signature(all_occupied_cells, symGroup)

                if assert_io:
                    for pl in placements_list:
                        assert all(isinstance(v, int) for v in pl.t), f"Non-int translation in solution: {pl.t}"
                        for c in pl.covered:
                            assert all(isinstance(v, int) for v in c), f"Non-int cell in solution: {c}"

                yield {
                    "type": "solution",
                    "t_ms": int((time.time() - t0) * 1000),
                    "solution": {
                        "containerCidSha256": container_cid,
                        "lattice": "fcc",
                        "piecesUsed": pieces_used,
                        "placements": solution_placements,
                        "sid_state_sha256": "dfs_state",
                        "sid_route_sha256": "dfs_route",
                        "sid_state_canon_sha256": sid,
                    },
                }
                return

            # Quick infeasibility: remaining empties must be multiple of 4
            if (empty_count & 3) != 0:
                return

            # Hole pruning (R6)
            if should_prune_holes(state, hole_pruning):
                return

            # Select a target empty cell
            target = select_target_cell_mrv(state, mrv_window)
            if target is None:
                return

            # Generate candidates, honoring pivot piece type & orientation, and bag counts
            candidates: List[Placement] = []

            avail_types = [p for p in bag.counts.keys() if bag.get_count(p) > 0]
            if not avail_types:
                return

            pv_piece, pv_ori = current_pivot()
            order = sorted(avail_types)
            if pv_piece and pv_piece in order:
                order.remove(pv_piece)
                order.insert(0, pv_piece)

            for p_name in order:
                if bag.get_count(p_name) <= 0:
                    continue
                pdef = pieces_dict.get(p_name)
                if pdef is None or not pdef.orientations:
                    continue

                orientations = list(enumerate(pdef.orientations))
                # pivot orientation for the pivot piece first
                if p_name == pv_piece and 0 <= pv_ori < len(orientations):
                    pivot_item = orientations[pv_ori]
                    orientations = [pivot_item] + [item for i, item in enumerate(orientations) if i != pv_ori]

                orientations = tie_shuffle(orientations, seed=seed)

                for ori_idx, ori in orientations:
                    if time_limit > 0 and (time.time() - t0) >= time_limit:
                        return
                    if not ori:
                        continue

                    # NEW: try anchoring EVERY cell of the orientation to the target
                    # so we don't miss placements where the target matches ori[1], ori[2], or ori[3].
                    for anchor_cell in ori:
                        tx = target[0] - anchor_cell[0]
                        ty = target[1] - anchor_cell[1]
                        tz = target[2] - anchor_cell[2]

                        covered = tuple((tx + cx, ty + cy, tz + cz) for (cx, cy, cz) in ori)
                        
                        # Verify target is actually covered by this placement
                        if target not in covered:
                            continue
                            
                        pl = Placement(piece=p_name, ori_idx=ori_idx, t=(tx, ty, tz), covered=covered)

                        # (Optional) sanity asserts if you have assert_io on
                        if assert_io:
                            assert all(isinstance(v, int) for v in pl.t), f"Non-int t: {pl.t}"
                            for c in pl.covered:
                                assert all(isinstance(v, int) for v in c), f"Non-int covered: {c}"

                        if state.is_valid_placement(pl):
                            candidates.append(pl)
                        elif depth == 0 and assert_io and len(candidates) == 0:
                            # Debug first failed placement
                            print(f"[DFS][debug] Failed placement: piece={p_name}, ori={ori_idx}, t={pl.t}")
                            print(f"[DFS][debug] Covered cells: {pl.covered}")
                            for i, cell in enumerate(pl.covered):
                                if cell not in state.cell_to_index:
                                    print(f"[DFS][debug]   Cell {i} {cell} is outside container")
                                elif state.is_occupied(state.cell_to_index[cell]):
                                    print(f"[DFS][debug]   Cell {i} {cell} is already occupied")
                            break  # Only debug first failure per orientation

            # Debug: check for zero candidates at depth 0
            if depth == 0 and not candidates and assert_io:
                print(f"[DFS][debug] depth=0 produced zero candidates at target {target}")
                print(f"[DFS][debug] avail_types: {avail_types}")
                print(f"[DFS][debug] bag counts: {bag.counts}")
                if avail_types:
                    first_piece = avail_types[0]
                    pdef = pieces_dict.get(first_piece)
                    if pdef and pdef.orientations:
                        print(f"[DFS][debug] {first_piece} has {len(pdef.orientations)} orientations")
                        if pdef.orientations[0]:
                            print(f"[DFS][debug] first orientation: {pdef.orientations[0]}")
                    else:
                        print(f"[DFS][debug] {first_piece} has no orientations or piece def")

            # Explore candidates
            for pl in candidates:
                if bag.get_count(pl.piece) <= 0:
                    continue
                bag.use_piece(pl.piece)
                mask = state.place_piece(pl)
                if mask == 0:
                    bag.return_piece(pl.piece)
                    continue

                placement_stack.append((pl, mask))
                current_placement_stack = placement_stack.copy()

                for ev in dfs(depth + 1, placement_stack, bag):
                    yield ev
                    if solutions_found >= max_results:
                        break

                # Backtrack
                placement_stack.pop()
                state.remove_piece(mask)
                bag.return_piece(pl.piece)
                current_placement_stack = placement_stack.copy()

                if solutions_found >= max_results:
                    return

        # ------------- Root loop with restarts over the SAME integer inventory -------------
        while True:
            if time_limit > 0 and (time.time() - t0) >= time_limit:
                break
            if solutions_found >= max_results:
                break

            bag = PieceBag(piece_counts)  # fresh counts each restart
            state.occupied_mask = 0
            current_placement_stack = []

            try:
                last_restart_time = time.time()
                last_restart_nodes = nodes_explored

                for ev in dfs(0, [], bag):
                    yield ev
                    if solutions_found >= max_results:
                        break

                if solutions_found >= max_results:
                    break
                if pivot_cycle:
                    advance_pivot()
                    continue
                break

            except _RestartSignal:
                restart_count += 1
                advance_pivot()
                # loop continues with fresh state and bag

        if status_emitter:
            status_emitter.stop()

        final_metrics = {
            "solutions_found": solutions_found,
            "nodes_explored": nodes_explored,
            "time_elapsed": time.time() - t0,
            "max_depth_reached": max_depth_reached,
            "max_pieces_placed": max_pieces_placed,
            "restart_count": restart_count,
        }
        yield {"type": "done", "metrics": final_metrics}
