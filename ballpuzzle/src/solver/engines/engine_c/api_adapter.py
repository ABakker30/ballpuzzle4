"""API adapter for Engine-C to implement EngineProtocol."""

from typing import Iterator, Dict, Any, List
from ...engine_api import EngineProtocol, EngineOptions, SolveEvent
from .lattice_fcc import Int3, validate_fcc_connectivity
from .precompute import build_placement_data, validate_container_piece_fit
from .search import dfs_solve
from .rand import Rng
import time
import hashlib


class EngineCAdapter(EngineProtocol):
    """Engine-C adapter implementing the standard engine protocol."""
    
    name = "engine-c"
    
    def solve(self, container: Dict[str, Any], inventory: Dict[str, Any], 
              pieces: Dict[str, Any], options: EngineOptions) -> Iterator[SolveEvent]:
        """
        Solve using Engine-C with FCC-optimized algorithms.
        
        Args:
            container: Container specification with cells
            inventory: Piece inventory counts
            pieces: Piece definitions
            options: Engine options (seed, flags, etc.)
        
        Yields:
            SolveEvent: Progress and solution events
        """
        start_time = time.time()
        
        # Extract configuration from options
        seed = options.get("seed", 20250907)
        flags = options.get("flags", {})
        max_results = flags.get("max_results", 1)
        time_budget_s = flags.get("time_budget_s", 300.0)
        pruning_level = flags.get("pruning_level", "basic")
        shuffle_policy = flags.get("shuffle", "ties_only")
        snapshot_every_nodes = flags.get("snapshot_every_nodes", 10000)
        
        # Extract container cells
        container_cells = [tuple(cell) for cell in container.get("coordinates", container.get("cells", []))]
        if not container_cells:
            yield self._emit_done(start_time, seed, 0, 0, 0)
            return
        
        # Validate FCC connectivity (temporarily disabled for debugging)
        # if not validate_fcc_connectivity(container_cells):
        #     raise ValueError("Container cells do not form connected FCC structure")
        
        # Extract piece data
        pieces_data = {}
        piece_inventory = inventory.get("pieces", {})
        
        for piece_id, piece_def in pieces.items():
            if piece_id in piece_inventory and piece_inventory[piece_id] > 0:
                # Handle PieceDef objects from library_fcc_v1
                if hasattr(piece_def, 'atoms'):
                    piece_cells = list(piece_def.atoms)
                    pieces_data[piece_id] = piece_cells
                elif isinstance(piece_def, dict) and "cells" in piece_def:
                    piece_cells = [tuple(cell) for cell in piece_def["cells"]]
                    pieces_data[piece_id] = piece_cells
        
        # Validate piece fit (temporarily disabled for debugging)
        # if not validate_container_piece_fit(container_cells, pieces_data, piece_inventory):
        #     raise ValueError("Pieces do not fit exactly in container")
        
        # Build precomputed data
        (
            candidates, covers_by_cell, candidate_meta, all_mask,
            index_of_cell, cells_by_index, piece_cell_counts
        ) = build_placement_data(container_cells, pieces_data)
        
        
        if not candidates:
            yield self._emit_done(start_time, seed, 0, 0, 0)
            return
        
        # Initialize RNG
        rng = Rng(seed)
        
        # Solution and progress tracking
        solutions_found = 0
        
        # Use generator pattern for interruptible search
        search_generator = self._run_interruptible_search(
            candidates, covers_by_cell, candidate_meta, all_mask,
            cells_by_index, index_of_cell, piece_inventory,
            max_results, time_budget_s, pruning_level, shuffle_policy,
            rng, snapshot_every_nodes, start_time, seed
        )
        
        # Yield events as they come from the search
        for event in search_generator:
            yield event
    
    def _run_interruptible_search(self, candidates, covers_by_cell, candidate_meta, all_mask,
                                 cells_by_index, index_of_cell, piece_inventory,
                                 max_results, time_budget_s, pruning_level, shuffle_policy,
                                 rng, snapshot_every_nodes, start_time, seed):
        """Run search with standard yield-after-progress pattern."""
        from .search import dfs_solve
        
        solutions_found = 0
        solution_placements = []
        
        def on_solution(placements):
            nonlocal solutions_found, solution_placements
            solutions_found += 1
            solution_placements = placements  # Store the solution
        
        def on_progress(nodes, depth, elapsed):
            # Progress will be handled by the CLI layer
            return True  # Continue search
        
        # Use the proper DFS search
        stats = dfs_solve(
            candidates=candidates,
            covers_by_cell=covers_by_cell,
            candidate_meta=candidate_meta,
            all_mask=all_mask,
            cells_by_index=cells_by_index,
            index_of_cell=index_of_cell,
            inventory=piece_inventory,
            max_results=max_results,
            time_budget_s=time_budget_s,
            pruning_level=pruning_level,
            shuffle_policy=shuffle_policy,
            rng=rng,
            snapshot_every_nodes=snapshot_every_nodes,
            on_solution=on_solution,
            on_progress=on_progress
        )
        
        # Emit solution event if found
        if solutions_found > 0 and solution_placements:
            yield {
                "type": "solution",
                "v": 1,
                "t_ms": int((time.time() - start_time) * 1000),
                "solution": {
                    "placements": solution_placements,
                    "piecesUsed": piece_inventory
                }
            }
        
        # Emit final done event
        yield self._emit_done(start_time, seed, solutions_found, stats["nodes"], stats["pruned"])
    
    def _emit_done(self, start_time: float, seed: int, solutions: int, nodes: int, pruned: int):
        """Helper to emit done event."""
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "v": 1,
            "t_ms": elapsed_ms,
            "type": "done",
            "metrics": {
                "solutions": solutions,
                "nodes": nodes,
                "pruned": pruned,
                "bestDepth": 0,
                "smallMode": False,
                "symGroup": 1,
                "seed": seed
            }
        }
    
    def _compute_container_cid(self, container_cells: List[Int3]) -> str:
        """Compute container CID hash."""
        cells_str = str(sorted(container_cells))
        return hashlib.sha256(cells_str.encode()).hexdigest()
