"""Bitmask-optimized DFS engine for high-performance ball puzzle solving,
with minimal additions:
- Root-level timed/node restarts (pivot over start piece and optionally orientation)
- MRV window target-cell heuristic
- Hole-pruning modes (none | single_component | lt4) with legacy --hole4 alias
"""

import time
import uuid
from typing import Iterator, Dict, Any, Set, List, Tuple, Optional
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
from ...common.status_snapshot import Snapshot, StackItem, ContainerInfo, StatusV2, PlacedPiece, Cell, Metrics, now_ms, label_for_piece, expand_piece_to_cells
from ...common.status_emitter import StatusEmitter
import itertools

I3 = Tuple[int, int, int]


# ------------------------
# Local signal for restarts
# ------------------------
class _RestartSignal(Exception):
    pass


class BitmaskDFSState:
    """Efficient bitmask-based state representation for DFS search."""
    
    def __init__(self, container_cells: List[I3]):
        self.container_cells = container_cells
        self.num_cells = len(container_cells)
        
        # Create mapping between coordinates and bit indices
        self.cell_to_index = {cell: i for i, cell in enumerate(container_cells)}
        self.index_to_cell = {i: cell for i, cell in enumerate(container_cells)}
        
        # Precompute neighbor relationships as bitmasks
        self.neighbor_masks = {}
        for i, cell in enumerate(container_cells):
            neighbors = []
            for dx, dy, dz in FCC_NEIGHBORS:
                neighbor = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                if neighbor in self.cell_to_index:
                    neighbors.append(self.cell_to_index[neighbor])
            self.neighbor_masks[i] = bitset_from_indices(neighbors, self.num_cells)
        
        # Initialize state
        self.occupied_mask = 0
        self.seen_masks = SeenMasks()
    
    def is_occupied(self, cell_index: int) -> bool:
        """Check if a cell is occupied."""
        return bool(self.occupied_mask & (1 << cell_index))
    
    def place_piece(self, placement: Placement) -> int:
        """Place a piece and return the bitmask of newly occupied cells."""
        new_mask = 0
        for cell in placement.covered:
            if cell in self.cell_to_index:
                cell_index = self.cell_to_index[cell]
                new_mask |= (1 << cell_index)
        
        self.occupied_mask |= new_mask
        return new_mask
    
    def remove_piece(self, piece_mask: int):
        """Remove a piece by clearing its bitmask."""
        self.occupied_mask &= ~piece_mask
    
    def get_empty_cells(self) -> List[int]:
        """Get list of empty cell indices."""
        empty = []
        for i in range(self.num_cells):
            if not (self.occupied_mask & (1 << i)):
                empty.append(i)
        return empty
    
    def get_empty_mask(self) -> int:
        """Get bitmask of empty cells."""
        return ((1 << self.num_cells) - 1) & (~self.occupied_mask)
    
    def has_holes_single_component(self) -> bool:
        """Check if there's more than one connected component of empty cells."""
        empty_cells = set(self.get_empty_cells())
        if len(empty_cells) <= 1:
            return False
        
        # Find first connected component
        start_cell = next(iter(empty_cells))
        visited = set()
        queue = [start_cell]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # Check neighbors
            neighbor_mask = self.neighbor_masks.get(current, 0)
            for neighbor_idx in range(self.num_cells):
                if (neighbor_mask & (1 << neighbor_idx)) and neighbor_idx in empty_cells and neighbor_idx not in visited:
                    queue.append(neighbor_idx)
        
        # If we didn't visit all empty cells, there are multiple components
        return len(visited) < len(empty_cells)
    
    def has_holes_lt4(self) -> bool:
        """Check if any connected component of empty cells has size < 4."""
        empty_cells = set(self.get_empty_cells())
        if not empty_cells:
            return False
        
        visited = set()
        
        for cell_idx in empty_cells:
            if cell_idx in visited:
                continue
            
            # BFS to find connected component size
            component_size = 0
            queue = [cell_idx]
            component_visited = set()
            
            while queue:
                current = queue.pop(0)
                if current in component_visited:
                    continue
                
                component_visited.add(current)
                visited.add(current)
                component_size += 1
                
                # Early termination if component is large enough
                if component_size >= 4:
                    break
                
                # Check neighbors
                neighbor_mask = self.neighbor_masks.get(current, 0)
                for neighbor_idx in range(self.num_cells):
                    if (neighbor_mask & (1 << neighbor_idx)) and neighbor_idx in empty_cells and neighbor_idx not in component_visited:
                        queue.append(neighbor_idx)
            
            # If this component is too small, we have holes
            if component_size < 4:
                return True
        
        return False
    
    def count_empty_cells(self) -> int:
        """Count number of empty cells using popcount."""
        return popcount(self.get_empty_mask())
    
    def get_first_empty_cell(self) -> I3:
        """Get first empty cell coordinate."""
        empty_mask = self.get_empty_mask()
        for i in range(self.num_cells):
            if empty_mask & (1 << i):
                return self.index_to_cell[i]
        return None
    
    def is_valid_placement(self, placement: Placement) -> bool:
        """Check if a placement is valid (no collisions)."""
        for cell in placement.covered:
            if cell in self.cell_to_index:
                cell_index = self.cell_to_index[cell]
                if self.is_occupied(cell_index):
                    return False
            else:
                return False  # Cell outside container
        return True


class DFSEngine(EngineProtocol):
    name = "dfs"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        import time
        t0 = time.time()
        start_time_ms = now_ms()
        seed = int(options.get("seed", 0))
        time_limit = float(options.get("time_limit", float('inf')))
        max_results = int(options.get("max_results", 1))
        
        # Enhanced DFS options
        restart_interval_s = float(options.get("restart_interval_s", 30.0))
        restart_nodes = int(options.get("restart_nodes", 100000))
        pivot_cycle = bool(options.get("pivot_cycle", True))
        mrv_window = int(options.get("mrv_window", 0))  # 0 = disabled
        hole_pruning = options.get("hole_pruning", "none")  # none | single_component | lt4
        
        # Legacy hole4 alias
        if options.get("hole4", False):
            hole_pruning = "lt4"
        
        # Status snapshot parameters
        status_json = options.get("status_json")
        status_interval_ms = options.get("status_interval_ms", 1000)
        status_max_stack = options.get("status_max_stack", 512)
        status_phase = options.get("status_phase")
        
        # Generate run ID
        run_id = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
        
        # Container info for status
        container_cid = container.get("cid_sha256", f"container_{hash(str(container))}")
        container_cells_count = len(container["coordinates"])
        
        # Load pieces and create inventory
        pieces_dict = load_fcc_A_to_Y()
        piece_counts = inventory.get("pieces", inventory)
        
        # Initialize bitmask state
        container_cells = sorted(tuple(map(int,c)) for c in container["coordinates"])
        state = BitmaskDFSState(container_cells)
        symGroup = container_symmetry_group(container_cells)
        
        # Calculate pieces needed
        container_size = len(container_cells)
        pieces_needed = container_size // 4
        
        # Initialize shared state
        solutions_found = 0
        nodes_explored = 0
        max_depth_reached = 0
        max_pieces_placed = 0
        current_placement_stack = []
        restart_count = 0
        last_restart_time = t0
        last_restart_nodes = 0
        
        # Pivot state for cycling through start pieces and orientations
        available_piece_names = sorted(piece_counts.keys())
        pivot_pieces = [(piece, 0) for piece in available_piece_names]  # (piece, orientation_idx)
        pivot_idx = 0
        
        def advance_pivot(pivot_pieces):
            nonlocal pivot_idx
            if not pivot_cycle or not pivot_pieces:
                return
            pivot_idx = (pivot_idx + 1) % len(pivot_pieces)
        
        def get_current_pivot():
            if not pivot_pieces:
                return None, 0
            return pivot_pieces[pivot_idx]
        
        # Status snapshot builder function
        def build_snapshot() -> StatusV2:
            try:
                placed_pieces = []
                instance_id = 1
                
                for pl, _ in current_placement_stack:
                    piece_names = sorted(pieces_dict.keys())
                    piece_name_to_idx = {name: idx for idx, name in enumerate(piece_names)}
                    piece_type = piece_name_to_idx.get(pl.piece, 0)
                    piece_label = label_for_piece(piece_type)
                    
                    anchor = pl.covered[0] if pl.covered else (0, 0, 0)
                    cells = expand_piece_to_cells(piece_type, anchor[0], anchor[1], anchor[2])
                    
                    placed_pieces.append(PlacedPiece(
                        instance_id=instance_id,
                        piece_type=piece_type,
                        piece_label=piece_label,
                        cells=cells
                    ))
                    instance_id += 1
                
                truncated = False
                if len(placed_pieces) > status_max_stack:
                    placed_pieces = placed_pieces[-status_max_stack:]
                    truncated = True
                
                elapsed = now_ms() - start_time_ms
                
                metrics = Metrics(
                    nodes=int(nodes_explored),
                    pruned=0,
                    depth=int(len(current_placement_stack)),
                    solutions=int(solutions_found),
                    elapsed_ms=int(elapsed),
                    best_depth=int(max_depth_reached) if max_depth_reached > 0 else None
                )
                
                return StatusV2(
                    version=2,
                    ts_ms=now_ms(),
                    engine="dfs",
                    phase=status_phase or "search",
                    run_id=run_id,
                    container=ContainerInfo(cid=container_cid, cells=container_cells_count),
                    metrics=metrics,
                    stack=placed_pieces,
                    stack_truncated=truncated
                )
                
            except Exception as e:
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
                    stack_truncated=False
                )
        
        # Initialize status emitter if requested
        status_emitter = None
        if status_json:
            try:
                status_emitter = StatusEmitter(status_json, status_interval_ms)
                status_emitter.start(build_snapshot)
            except Exception as e:
                pass
        
        # Generate piece combinations using greedy approach
        def generate_piece_combinations_chunked(container_size: int, available_pieces: Dict[str, int], max_combinations: int = 1000):
            pieces_needed = container_size // 4
            if container_size % 4 != 0:
                return []
            
            # For large containers, use single combination approach
            if pieces_needed > 10:
                total_available = sum(available_pieces.values())
                if total_available < pieces_needed:
                    return []
                
                combo = {}
                pieces_assigned = 0
                for piece in sorted(available_pieces.keys()):
                    if pieces_assigned >= pieces_needed:
                        break
                    count = min(available_pieces[piece], pieces_needed - pieces_assigned)
                    if count > 0:
                        combo[piece] = count
                        pieces_assigned += count
                
                return [combo] if pieces_assigned == pieces_needed else []
            
            # For smaller containers, use greedy approach prioritizing known working combinations
            combinations = []
            
            # Prioritize known working combinations first
            working_combos = [
                {'A': 2, 'E': 1, 'T': 1},
                {'A': 1, 'E': 1, 'T': 2},
                {'E': 2, 'T': 2},
            ]
            
            for combo in working_combos:
                if sum(combo.values()) == pieces_needed:
                    valid = True
                    for piece, count_needed in combo.items():
                        if available_pieces.get(piece, 0) < count_needed:
                            valid = False
                            break
                    if valid:
                        combinations.append(combo)
            
            # Add other combinations using itertools
            from itertools import combinations as iter_combinations
            piece_names = list(available_pieces.keys())
            
            if len(piece_names) >= pieces_needed:
                count = 0
                for combo in iter_combinations(piece_names, pieces_needed):
                    count += 1
                    if count > max_combinations:
                        break
                    
                    piece_count = {piece: 1 for piece in combo}
                    if piece_count not in combinations:
                        combinations.append(piece_count)
            
            return combinations
        
        valid_combinations = generate_piece_combinations_chunked(container_size, piece_counts)
        
        if not valid_combinations:
            if status_emitter:
                status_emitter.stop()
            yield {
                "type": "done",
                "metrics": {
                    "solutions_found": 0,
                    "nodes_explored": 0,
                    "time_elapsed": time.time() - t0
                }
            }
            return
        
        # Select target cell using MRV heuristic
        def select_target_cell_mrv(state: BitmaskDFSState, window_size: int) -> Optional[I3]:
            if window_size <= 0:
                return state.get_first_empty_cell()
            
            empty_cells = state.get_empty_cells()
            if not empty_cells:
                return None
            
            # Calculate remaining values (neighbor count) for each empty cell
            cell_scores = []
            for cell_idx in empty_cells[:window_size]:  # Only consider window
                neighbor_mask = state.neighbor_masks.get(cell_idx, 0)
                empty_neighbors = 0
                for i in range(state.num_cells):
                    if (neighbor_mask & (1 << i)) and not state.is_occupied(i):
                        empty_neighbors += 1
                cell_scores.append((empty_neighbors, cell_idx))
            
            # Select cell with minimum remaining values (most constrained)
            if cell_scores:
                _, best_cell_idx = min(cell_scores)
                return state.index_to_cell[best_cell_idx]
            
            return state.get_first_empty_cell()
        
        # Check hole pruning conditions
        def should_prune_holes(state: BitmaskDFSState, mode: str) -> bool:
            if mode == "none":
                return False
            elif mode == "single_component":
                return state.has_holes_single_component()
            elif mode == "lt4":
                return state.has_holes_lt4()
            return False
        
        # Main DFS search with restarts
        def dfs(depth: int, placement_stack: List[Tuple[Placement, int]], combo_bag: PieceBag) -> Iterator[SolveEvent]:
            nonlocal solutions_found, nodes_explored, max_depth_reached, max_pieces_placed, current_placement_stack
            nonlocal last_restart_time, last_restart_nodes, restart_count
            
            # Time limit check
            if time_limit > 0 and (time.time() - t0) >= time_limit:
                return
            
            # Restart conditions
            current_time = time.time()
            nodes_since_restart = nodes_explored - last_restart_nodes
            
            if ((current_time - last_restart_time) >= restart_interval_s or 
                nodes_since_restart >= restart_nodes):
                if depth > 0:  # Only restart from root
                    raise _RestartSignal()
            
            nodes_explored += 1
            max_depth_reached = max(max_depth_reached, depth)
            max_pieces_placed = max(max_pieces_placed, len(placement_stack))
            
            # Check if solved
            if state.count_empty_cells() == 0:
                solutions_found += 1
                
                placements_list = [pl for pl, _ in placement_stack]
                solution_placements = []
                all_occupied_cells = []
                
                for pl in placements_list:
                    solution_placements.append({
                        "piece": pl.piece,
                        "ori": pl.ori_idx,
                        "t": list(pl.t),
                        "cells_ijk": [list(coord) for coord in pl.covered]
                    })
                    all_occupied_cells.extend(pl.covered)
                
                pieces_used = {}
                for pl in placements_list:
                    pieces_used[pl.piece] = pieces_used.get(pl.piece, 0) + 1
                
                sid = canonical_state_signature(all_occupied_cells, symGroup)
                
                yield {
                    "type": "solution",
                    "t_ms": int((time.time()-t0)*1000),
                    "solution": {
                        "containerCidSha256": container.get("cid_sha256", "unknown"),
                        "lattice": "fcc",
                        "piecesUsed": pieces_used,
                        "placements": solution_placements,
                        "sid_state_sha256": "dfs_state",
                        "sid_route_sha256": "dfs_route", 
                        "sid_state_canon_sha256": sid
                    }
                }
                
                if solutions_found >= max_results:
                    return
                return
            
            # Early termination checks
            empty_count = state.count_empty_cells()
            if empty_count < 4:
                return  # Not enough space for any piece
            
            # Hole pruning
            if should_prune_holes(state, hole_pruning):
                return
            
            # Get target cell for placement
            target = select_target_cell_mrv(state, mrv_window)
            if target is None:
                return
        
            # Generate candidates with pivot preference
            candidates = []
            available_piece_names = [piece for piece in combo_bag.counts.keys() if combo_bag.get_count(piece) > 0]
            
            # Get current pivot piece and orientation
            pivot_piece, pivot_ori = get_current_pivot()
            
            # Prioritize pivot piece, then others
            piece_order = sorted(available_piece_names)
            if pivot_piece and pivot_piece in piece_order:
                piece_order.remove(pivot_piece)
                piece_order.insert(0, pivot_piece)
            
            for piece in piece_order:
                if combo_bag.get_count(piece) <= 0:
                    continue
                
                piece_def = pieces_dict.get(piece)
                if piece_def is None:
                    continue
                
                # For pivot piece, try pivot orientation first
                orientations = list(enumerate(piece_def.orientations))
                if piece == pivot_piece and pivot_ori < len(orientations):
                    # Move pivot orientation to front
                    pivot_item = orientations[pivot_ori]
                    orientations = [pivot_item] + [item for i, item in enumerate(orientations) if i != pivot_ori]
                
                for ori_idx, ori in orientations:
                    # Time limit check in innermost loop
                    if time_limit > 0 and (time.time() - t0) >= time_limit:
                        return
                    
                    if ori:  # Check if orientation has cells
                        first_cell = ori[0]
                        t = (target[0] - first_cell[0], target[1] - first_cell[1], target[2] - first_cell[2])
                        covered = tuple((t[0] + cell[0], t[1] + cell[1], t[2] + cell[2]) for cell in ori)
                        pl = Placement(piece=piece, ori_idx=ori_idx, t=t, covered=covered)
                        
                        if state.is_valid_placement(pl):
                            candidates.append(pl)
            
            # Try each candidate
            for pl in candidates:
                if combo_bag.get_count(pl.piece) <= 0:
                    continue
                
                # Place piece
                combo_bag.use_piece(pl.piece)
                piece_mask = state.place_piece(pl)
                placement_stack.append((pl, piece_mask))
                
                # Update current placement stack for status snapshots
                current_placement_stack = placement_stack.copy()
                
                # Recurse
                for ev in dfs(depth + 1, placement_stack, combo_bag):
                    yield ev
                    if solutions_found >= max_results:
                        return
                
                # Backtrack
                placement_stack.pop()
                state.remove_piece(piece_mask)
                combo_bag.return_piece(pl.piece)
                
                # Update current placement stack for status snapshots
                current_placement_stack = placement_stack.copy()
        
        # Main search loop with restarts
        for combo_idx, target_inventory in enumerate(valid_combinations):
            # Check time and result limits
            if time_limit > 0 and (time.time() - t0) >= time_limit:
                break
            if solutions_found >= max_results:
                break
            
            # Initialize inventory bag for this combination
            combo_bag = PieceBag(target_inventory)
            
            # Reset state for new combination
            state.occupied_mask = 0
            
            # Restart loop for this combination
            while True:
                try:
                    # Update restart tracking
                    last_restart_time = time.time()
                    last_restart_nodes = nodes_explored
                    
                    # Start search for this combination
                    for ev in dfs(0, [], combo_bag):
                        yield ev
                        if solutions_found >= max_results:
                            break
                    
                    # If we get here, search completed without restart
                    break
                    
                except _RestartSignal:
                    # Handle restart
                    restart_count += 1
                    advance_pivot(pivot_pieces)
                    
                    # Reset state for restart
                    state.occupied_mask = 0
                    combo_bag = PieceBag(target_inventory)  # Reset inventory
                    current_placement_stack = []
                    
                    # Check limits before restarting
                    if time_limit > 0 and (time.time() - t0) >= time_limit:
                        break
                    if solutions_found >= max_results:
                        break
                    
                    # Continue with restart
                    continue
            
            if solutions_found >= max_results:
                break
        
        # Stop status emitter if running
        if status_emitter:
            status_emitter.stop()
        
        # Emit final done event
        final_metrics = {
            "solutions_found": solutions_found,
            "nodes_explored": nodes_explored,
            "time_elapsed": time.time() - t0,
            "max_depth_reached": max_depth_reached,
            "max_pieces_placed": max_pieces_placed,
            "restart_count": restart_count
        }
        
        yield {
            "type": "done",
            "metrics": final_metrics
        }
