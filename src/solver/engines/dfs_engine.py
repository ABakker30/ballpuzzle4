"""Bitmask-optimized DFS engine for high-performance ball puzzle solving."""

import time
import uuid
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
from ...common.status_snapshot import Snapshot, StackItem, ContainerInfo, StatusV2, PlacedPiece, Cell, Metrics, now_ms, label_for_piece, expand_piece_to_cells
from ...common.status_emitter import StatusEmitter
import itertools

I3 = Tuple[int, int, int]

class BitmaskDFSState:
    """Efficient bitmask-based state representation for DFS search."""
    
    def __init__(self, container_cells: List[I3]):
        self.container_cells = container_cells
        self.num_cells = len(container_cells)
        
        # Create mapping between coordinates and bit indices
        self.cell_to_index = {cell: i for i, cell in enumerate(container_cells)}
        self.index_to_cell = {i: cell for i, cell in enumerate(container_cells)}
        
        # Container bitmask (all cells available initially)
        self.container_mask = (1 << self.num_cells) - 1
        
        # Occupied cells bitmask (starts empty)
        self.occupied_mask = 0
        
        # Precompute FCC neighbor mappings for efficient connectivity checks
        self.neighbor_masks = self._precompute_neighbor_masks()
    
    def _precompute_neighbor_masks(self) -> Dict[int, int]:
        """Precompute neighbor bitmasks for each cell index."""
        neighbor_masks = {}
        
        for i, cell in enumerate(self.container_cells):
            neighbor_mask = 0
            for dx, dy, dz in FCC_NEIGHBORS:
                neighbor_coord = (cell[0] + dx, cell[1] + dy, cell[2] + dz)
                if neighbor_coord in self.cell_to_index:
                    neighbor_idx = self.cell_to_index[neighbor_coord]
                    neighbor_mask |= (1 << neighbor_idx)
            neighbor_masks[i] = neighbor_mask
        
        return neighbor_masks
    
    def get_empty_mask(self) -> int:
        """Get bitmask of empty (unoccupied) cells."""
        return self.container_mask & (~self.occupied_mask)
    
    def place_piece(self, placement: Placement) -> int:
        """Place a piece and return the bitmask of newly occupied cells."""
        piece_mask = 0
        for coord in placement.covered:
            if coord in self.cell_to_index:
                idx = self.cell_to_index[coord]
                piece_mask |= (1 << idx)
        
        self.occupied_mask |= piece_mask
        return piece_mask
    
    def remove_piece(self, piece_mask: int):
        """Remove a piece using its bitmask."""
        self.occupied_mask &= (~piece_mask)
    
    def is_valid_placement(self, placement: Placement) -> bool:
        """Check if placement is valid (all cells in container and unoccupied)."""
        for coord in placement.covered:
            if coord not in self.cell_to_index:
                return False
            idx = self.cell_to_index[coord]
            if self.occupied_mask & (1 << idx):
                return False
        return True
    
    def has_disconnected_holes(self) -> bool:
        """Fast bitmask-based hole detection using flood-fill."""
        empty_mask = self.get_empty_mask()
        if empty_mask == 0:
            return False
        
        # Find first empty cell
        first_empty_idx = -1
        for i in range(self.num_cells):
            if empty_mask & (1 << i):
                first_empty_idx = i
                break
        
        if first_empty_idx == -1:
            return False
        
        # Flood-fill from first empty cell using bitmask operations
        visited_mask = 0
        queue_mask = 1 << first_empty_idx
        
        while queue_mask != 0:
            # Get next cell from queue (find first set bit)
            current_idx = -1
            for i in range(self.num_cells):
                if queue_mask & (1 << i):
                    current_idx = i
                    break
            
            if current_idx == -1:
                break
            
            # Remove from queue and mark visited
            queue_mask &= ~(1 << current_idx)
            visited_mask |= (1 << current_idx)
            
            # Add unvisited empty neighbors to queue
            neighbor_mask = self.neighbor_masks[current_idx]
            unvisited_empty_neighbors = neighbor_mask & empty_mask & (~visited_mask)
            queue_mask |= unvisited_empty_neighbors
        
        # Check if all empty cells were visited
        return visited_mask != empty_mask
    
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

class DFSEngine(EngineProtocol):
    name = "dfs"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        import time
        t0 = time.time()
        start_time_ms = now_ms()
        seed = int(options.get("seed", 0))
        time_limit = float(options.get("time_limit", float('inf')))
        max_results = int(options.get("max_results", 1))
        use_hole4_detection = bool(options.get("hole4", False))
        
        # Piece rotation strategy parameters
        piece_rotation_interval = options.get("piece_rotation_interval", 5.0)  # seconds
        
        # Status snapshot parameters
        status_json = options.get("status_json")
        status_interval_ms = options.get("status_interval_ms", 1000)
        status_max_stack = options.get("status_max_stack", 512)
        status_phase = options.get("status_phase")
        
        # Debug status options to file
        with open("dfs_debug.log", "w") as f:
            f.write(f"DEBUG: All options keys: {list(options.keys())}\n")
            f.write(f"DEBUG: status_json option: {status_json}\n")
            if status_json:
                f.write(f"DEBUG: Status JSON enabled - file: {status_json}, interval: {status_interval_ms}ms\n")
        
        # Generate run ID
        run_id = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
        
        # Container info for status
        container_cid = container.get("cid_sha256", f"container_{hash(str(container))}")
        container_cells_count = len(container["coordinates"])
        
        # Load pieces and create inventory
        pieces_dict = load_fcc_A_to_Y()
        # Extract piece counts from inventory format
        piece_counts = inventory.get("pieces", inventory)
        bag = PieceBag(piece_counts)
        
        # Initialize bitmask state
        container_cells = sorted(tuple(map(int,c)) for c in container["coordinates"])
        state = BitmaskDFSState(container_cells)
        symGroup = container_symmetry_group(container_cells)
        
        # Calculate pieces needed
        container_size = len(container_cells)
        pieces_needed = container_size // 4
        
        # Initialize shared state for status snapshots
        solutions_found = 0
        nodes_explored = 0
        max_depth_reached = 0
        max_pieces_placed = 0
        # Initialize current placement stack for status snapshots
        current_placement_stack = []
        next_instance_id = 1  # v2: stable instance IDs
        
        # Create piece name to index mapping for status snapshots
        piece_names = sorted(pieces_dict.keys())
        piece_name_to_idx = {name: idx for idx, name in enumerate(piece_names)}
        
        # Status snapshot builder function (v2)
        def build_snapshot() -> StatusV2:
            try:
                # Convert placement stack to PlacedPiece format with instance IDs
                placed_pieces = []
                instance_id = 1
                
                for pl, _ in current_placement_stack:
                    piece_type = piece_name_to_idx.get(pl.piece, 0)
                    piece_label = label_for_piece(piece_type)
                    
                    # Use anchor cell (first coordinate) for position
                    anchor = pl.covered[0] if pl.covered else (0, 0, 0)
                    
                    # Expand piece to all 4 cells
                    cells = expand_piece_to_cells(piece_type, anchor[0], anchor[1], anchor[2])
                    
                    placed_pieces.append(PlacedPiece(
                        instance_id=instance_id,
                        piece_type=piece_type,
                        piece_label=piece_label,
                        cells=cells
                    ))
                    instance_id += 1
                
                # Apply stack truncation if needed (truncate pieces, not cells)
                truncated = False
                if len(placed_pieces) > status_max_stack:
                    placed_pieces = placed_pieces[-status_max_stack:]  # keep tail
                    truncated = True
                
                elapsed = now_ms() - start_time_ms
                
                metrics = Metrics(
                    nodes=int(nodes_explored),
                    pruned=0,  # DFS doesn't track pruned separately
                    depth=int(len(current_placement_stack)),
                    solutions=int(solutions_found),
                    elapsed_ms=int(elapsed),
                    best_depth=int(max_depth_reached) if max_depth_reached > 0 else None
                )
                
                snapshot = StatusV2(
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
                
                return snapshot
                
            except Exception as e:
                # Return a minimal v2 snapshot on error
                metrics = Metrics(
                    nodes=0, pruned=0, depth=0, solutions=0, elapsed_ms=0
                )
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
                with open("dfs_debug.log", "a") as f:
                    f.write(f"DEBUG: Creating StatusEmitter with file: {status_json}\n")
                status_emitter = StatusEmitter(status_json, status_interval_ms)
                with open("dfs_debug.log", "a") as f:
                    f.write(f"DEBUG: StatusEmitter created, starting...\n")
                status_emitter.start(build_snapshot)
                with open("dfs_debug.log", "a") as f:
                    f.write(f"DEBUG: StatusEmitter started successfully\n")
            except Exception as e:
                with open("dfs_debug.log", "a") as f:
                    f.write(f"DEBUG: Error creating/starting StatusEmitter: {e}\n")
        
        # Generate piece combinations with chunking and time limits
        def generate_piece_combinations_chunked(container_size: int, available_pieces: Dict[str, int], max_combinations: int = 10000):
            """Generate piece combinations incrementally to avoid exponential explosion."""
            pieces_needed = container_size // 4
            if container_size % 4 != 0:
                return []  # Container size must be divisible by 4
            
            # For large containers, use a simplified approach
            if pieces_needed > 10:
                # Check if we have enough total pieces
                total_available = sum(available_pieces.values())
                if total_available < pieces_needed:
                    return []  # Not enough pieces available
                
                # Use all available pieces approach for large containers
                combinations = []
                piece_names = list(available_pieces.keys())
                
                # Create combination using all available pieces up to what's needed
                combo = {}
                pieces_assigned = 0
                for piece in piece_names:
                    if pieces_assigned >= pieces_needed:
                        break
                    count = min(available_pieces[piece], pieces_needed - pieces_assigned)
                    if count > 0:
                        combo[piece] = count
                        pieces_assigned += count
                
                if pieces_assigned == pieces_needed:
                    combinations.append(combo)
                
                return combinations
            
            # For smaller containers, use full enumeration but with limits
            from itertools import combinations_with_replacement
            
            combinations = []
            piece_names = list(available_pieces.keys())
            
            # Limit enumeration to prevent explosion
            count = 0
            for combo in combinations_with_replacement(piece_names, pieces_needed):
                count += 1
                if count > max_combinations * 10:  # Safety limit
                    break
                    
                # Count pieces in this combination
                piece_count = {}
                for piece in combo:
                    piece_count[piece] = piece_count.get(piece, 0) + 1
                
                # Check if we have enough inventory
                valid = True
                for piece, count_needed in piece_count.items():
                    if available_pieces.get(piece, 0) < count_needed:
                        valid = False
                        break
                
                if valid:
                    combinations.append(piece_count)
                    if len(combinations) >= max_combinations:
                        break
            
            return combinations
        
        # Get available pieces from inventory
        inv = piece_counts
        valid_combinations = generate_piece_combinations_chunked(container_size, inv)
        
        # Prioritize known working combinations
        working_combos = [
            {'A': 2, 'E': 1, 'T': 1},  # Known working
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
        
        # Piece rotation strategy - cycle through starting pieces
        available_pieces = sorted(set().union(*valid_combinations))
        current_piece_idx = 0
        last_rotation_time = t0
        
        # Try each combination until solution found or time/result limit reached
        for combo_idx, target_inventory in enumerate(valid_combinations):
            # Check time and result limits before trying new combination
            if time_limit > 0 and (time.time() - t0) >= time_limit:
                break
            if solutions_found >= max_results:
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
            combo_bag = PieceBag(target_inventory)
            
            # Reset state for new combination
            state.occupied_mask = 0
            
            def dfs(depth: int, placement_stack: List[Tuple[Placement, int]]) -> Iterator[SolveEvent]:
                nonlocal solutions_found, nodes_explored, max_depth_reached, max_pieces_placed, current_placement_stack, next_instance_id
                
                # Time limit check
                if time_limit > 0 and (time.time() - t0) >= time_limit:
                    print(f"DEBUG: Time limit reached - depth={depth}, pieces_placed={len(placement_stack)}, nodes={nodes_explored}")
                    return
                
                nodes_explored += 1
                max_depth_reached = max(max_depth_reached, depth)
                max_pieces_placed = max(max_pieces_placed, len(placement_stack))
                
                # Progress reporting every 50000 nodes
                if nodes_explored % 50000 == 0:
                    print(f"DEBUG: Progress - nodes={nodes_explored}, depth={depth}, pieces_placed={len(placement_stack)}, time={time.time() - t0:.1f}s")
                
                # Check if solved
                if state.count_empty_cells() == 0:
                    # Found solution
                    solutions_found += 1
                    
                    # Convert placements to solution format
                    placements_list = [pl for pl, _ in placement_stack]
                    
                    # Create solution placements in the expected format
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
                    
                    # Count pieces used
                    pieces_used = {}
                    for pl in placements_list:
                        pieces_used[pl.piece] = pieces_used.get(pl.piece, 0) + 1
                    
                    sid = canonical_state_signature(all_occupied_cells, symGroup)
                    
                    yield {
                        "type": "solution",
                        "t_ms": int((time.time()-t0)*1000),
                        "solution": {
                            "containerCidSha256": container["cid_sha256"],
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
                
                # Hole4 detection
                if use_hole4_detection and depth > 0:
                    if state.has_disconnected_holes():
                        return
                
                # Get target cell for placement
                target = state.get_first_empty_cell()
                if target is None:
                    return
            
                # Generate candidates with piece rotation priority
                candidates = []
                available_piece_names = list(combo_bag.counts.keys())
                
                # Prioritize the preferred starting piece, then others
                piece_order = sorted(available_piece_names)
                if preferred_start_piece and preferred_start_piece in piece_order:
                    piece_order.remove(preferred_start_piece)
                    piece_order.insert(0, preferred_start_piece)
                
                for piece in piece_order:
                    if combo_bag.get_count(piece) <= 0:
                        continue
                    
                    piece_def = pieces_dict.get(piece)
                    if piece_def is None:
                        continue
                    
                    for ori_idx, ori in enumerate(piece_def.orientations):
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
                    for ev in dfs(depth + 1, placement_stack):
                        yield ev
                        if solutions_found >= max_results:
                            return
                    
                    # Backtrack
                    placement_stack.pop()
                    state.remove_piece(piece_mask)
                    combo_bag.return_piece(pl.piece)
                    
                    # Update current placement stack for status snapshots
                    current_placement_stack = placement_stack.copy()
            
            # Start search for this combination
            for ev in dfs(0, []):
                yield ev
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
            "max_pieces_placed": max_pieces_placed
        }
        print(f"DEBUG: Final metrics - {final_metrics}")
        yield {
            "type": "done",
            "metrics": final_metrics
        }
