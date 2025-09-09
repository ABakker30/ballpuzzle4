"""Bitmask-optimized DFS engine for high-performance ball puzzle solving."""

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

class DFSBitmaskEngine(EngineProtocol):
    name = "dfs-bitmask"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        import time
        t0 = time.time()
        seed = int(options.get("seed", 0))
        time_limit = float(options.get("time_limit", float('inf')))
        max_results = int(options.get("max_results", 1))
        use_hole4_detection = bool(options.get("hole4", False))
        
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
        
        # Generate piece combinations like DFS engine
        def generate_piece_combinations(container_size: int, available_pieces: Dict[str, int]):
            """Generate all piece combinations that sum to exactly container_size cells."""
            pieces_needed = container_size // 4
            if container_size % 4 != 0:
                return []  # Container size must be divisible by 4
            
            from itertools import combinations_with_replacement
            
            # Generate all possible combinations
            combinations = []
            piece_names = list(available_pieces.keys())
            
            # Use combinations_with_replacement to generate all possible combinations
            for combo in combinations_with_replacement(piece_names, pieces_needed):
                # Count pieces in this combination
                piece_count = {}
                for piece in combo:
                    piece_count[piece] = piece_count.get(piece, 0) + 1
                
                # Check if we have enough inventory
                valid = True
                for piece, count in piece_count.items():
                    if available_pieces.get(piece, 0) < count:
                        valid = False
                        break
                
                if valid:
                    combinations.append(piece_count)
            
            return combinations
        
        # Get available pieces from inventory
        inv = piece_counts
        valid_combinations = generate_piece_combinations(container_size, inv)
        
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
            yield {
                "type": "done",
                "metrics": {
                    "solutions_found": 0,
                    "nodes_explored": 0,
                    "time_elapsed": time.time() - t0
                }
            }
            return
        
        solutions_found = 0
        nodes_explored = 0
        
        # Try each combination until solution found or time/result limit reached
        for combo_idx, target_inventory in enumerate(valid_combinations):
            # Check time and result limits before trying new combination
            if time_limit > 0 and (time.time() - t0) >= time_limit:
                break
            if solutions_found >= max_results:
                break
            
            # Initialize inventory bag for this combination
            combo_bag = PieceBag(target_inventory)
            
            # Reset state for new combination
            state.occupied_mask = 0
            
            
            def dfs(depth: int, placement_stack: List[Tuple[Placement, int]]) -> Iterator[SolveEvent]:
                nonlocal solutions_found, nodes_explored
                
                # Time limit check
                if time.time() - t0 > time_limit:
                    return
                
                nodes_explored += 1
                
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
                    
                    sid = canonical_state_signature(all_occupied_cells, symGroup)
                    
                    yield {
                        "type": "solution",
                        "solution": {
                            "placements": solution_placements,
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
            
                # Generate candidates
                candidates = []
                available_pieces = list(combo_bag.counts.keys())
                for piece in sorted(available_pieces):
                    if combo_bag.get_count(piece) <= 0:
                        continue
                    
                    piece_def = pieces_dict.get(piece)
                    if piece_def is None:
                        continue
                    
                    for ori_idx, ori in enumerate(piece_def.orientations):
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
                    
                    # Recurse
                    for ev in dfs(depth + 1, placement_stack):
                        yield ev
                        if solutions_found >= max_results:
                            return
                    
                    # Backtrack
                    placement_stack.pop()
                    state.remove_piece(piece_mask)
                    combo_bag.return_piece(pl.piece)
            
            # Start search for this combination
            for ev in dfs(0, []):
                yield ev
                if solutions_found >= max_results:
                    break
        
        # Emit done event
        yield {
            "type": "done",
            "metrics": {
                "solutions_found": solutions_found,
                "nodes_explored": nodes_explored,
                "time_elapsed": time.time() - t0
            }
        }
