from typing import Iterator, List, Tuple, Dict, Any, Set
import time
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...solver.tt import OccMask, SeenMasks
from ...solver.symbreak import container_symmetry_group, anchor_rule_filter
from ...solver.heuristics import tie_shuffle
from ...solver.placement_gen import for_target, Placement
from ...solver.utils import first_empty_cell
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...pieces.inventory import PieceBag
from ...io.solution_sig import canonical_state_signature, extract_occupied_cells_from_placements

I3 = Tuple[int,int,int]

class DFSEngine(EngineProtocol):
    name = "dfs"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        """
        Real DFS with A-Y piece placements:
        - order cells canonically (sorted)
        - depth-first search with real piece placements
        - use TT to prune duplicate masks
        - at depth 0, apply anchor_rule_filter to placement candidates
        - tie-shuffle candidate order with seed
        - respect inventory counts
        - find multiple solutions with canonical deduplication
        """
        t0 = time.time()
        seed = int(options.get("seed", 0))
        max_results = int(options.get("max_results", 1))
        cells: List[I3] = sorted(tuple(map(int,c)) for c in container["coordinates"])
        container_set = set(cells)
        smallMode = len(cells) <= 32
        symGroup = container_symmetry_group(cells)
        symGroupSize = len(symGroup)
        tt = SeenMasks()
        occ = OccMask(cells)
        
        # Load piece library and create inventory bag
        piece_lib = load_fcc_A_to_Y()
        bag = PieceBag(inventory.get("pieces", {}))
        
        # Track emitted solution signatures for deduplication
        emitted_sigs: Set[str] = set()
        solutions_found = 0
        
        # Placement stack for backtracking
        placement_stack: List[Tuple[str, int, I3, List[I3]]] = []

        nodes = pruned = 0
        bestDepth = 0

        class StopSearch(Exception):
            pass

        def dfs(depth: int) -> None:
            nonlocal nodes, pruned, bestDepth, solutions_found
            bestDepth = max(bestDepth, depth)

            # Check if we've found enough solutions
            if solutions_found >= max_results:
                raise StopSearch()

            # Find next empty cell
            target = first_empty_cell(occ, cells)
            if target is None:
                # All cells filled - found a solution
                # Build solution from placement stack
                final_placements = []
                for piece, ori_idx, t, covered in placement_stack:
                    placement_dict = {
                        "piece": piece,
                        "ori": ori_idx,
                        "t": list(t),
                        "coordinates": [list(coord) for coord in covered]
                    }
                    final_placements.append(placement_dict)
                
                # Compute canonical signature for deduplication
                occupied_cells = []
                for _, _, _, covered in placement_stack:
                    occupied_cells.extend(covered)
                sig = canonical_state_signature(occupied_cells, symGroup)
                
                # Check if we've already emitted this canonical solution
                if sig not in emitted_sigs:
                    emitted_sigs.add(sig)
                    solutions_found += 1
                    
                    sol = {
                        "containerCidSha256": container.get("cid_sha256", "unknown"),
                        "lattice": "fcc",
                        "piecesUsed": {k: inventory.get("pieces", {}).get(k, 0) - bag.get_count(k) 
                                      for k in inventory.get("pieces", {})},
                        "placements": final_placements,
                        "sid_state_sha256": "dfs_real_state",
                        "sid_route_sha256": "dfs_real_route", 
                        "sid_state_canon_sha256": sig,
                    }
                    yield {"t_ms": int((time.time()-t0)*1000), "type": "solution", "solution": sol}
                return

            # Generate real piece placements for target cell
            placements = for_target(target, occ, bag, piece_lib, container_set, seed, depth)
            
            for placement in placements:
                nodes += 1
                
                # Check transposition table
                old_mask = occ.mask
                occ.set_cells(placement.covered)
                
                if not tt.check_and_add(occ.mask):
                    pruned += 1
                    occ.mask = old_mask
                    continue
                
                # Update inventory
                bag.use_piece(placement.piece, 1)
                
                # Push to placement stack
                placement_stack.append((placement.piece, placement.ori_idx, placement.t, placement.covered))
                
                # Recurse
                try:
                    yield from dfs(depth + 1)
                except StopSearch:
                    # Pop and restore state before re-raising
                    placement_stack.pop()
                    bag.return_piece(placement.piece, 1)
                    occ.mask = old_mask
                    raise
                
                # Backtrack
                placement_stack.pop()
                bag.return_piece(placement.piece, 1)
                occ.mask = old_mask

        # Run DFS search
        try:
            yield from dfs(0)
        except StopSearch:
            pass

        # Always emit done event
        yield {"t_ms": int((time.time()-t0)*1000), "type": "done",
               "metrics": {"solutions": solutions_found, "nodes": nodes, "pruned": pruned,
                           "bestDepth": bestDepth, "smallMode": smallMode, "symGroup": symGroupSize, "seed": seed}}
