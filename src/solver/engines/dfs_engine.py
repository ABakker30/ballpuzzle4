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
        """
        t0 = time.time()
        seed = int(options.get("seed", 0))
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
        
        # Track placements for solution
        solution_placements: List[Dict[str, Any]] = []

        nodes = pruned = 0
        bestDepth = 0

        def dfs(depth: int) -> bool:
            nonlocal nodes, pruned, bestDepth
            bestDepth = max(bestDepth, depth)

            # Find next empty cell
            target = first_empty_cell(occ, cells)
            if target is None:
                # All cells filled - found a solution
                return True

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
                
                # Add to solution placements
                placement_dict = {
                    "piece": placement.piece,
                    "ori": placement.ori_idx,
                    "t": list(placement.t),
                    "coordinates": [list(coord) for coord in placement.covered]
                }
                solution_placements.append(placement_dict)
                
                # Recurse
                if dfs(depth + 1):
                    return True
                
                # Backtrack
                solution_placements.pop()
                bag.return_piece(placement.piece, 1)
                occ.mask = old_mask

            return False

        # Run DFS search
        solved = dfs(0)

        # Always emit a solution event for backward compatibility
        final_cells = cells if solved else []
        final_placements = solution_placements if solved else []
        sig = canonical_state_signature(final_cells, symGroup)
        
        sol = {
            "containerCidSha256": container.get("cid_sha256", "unknown"),
            "lattice": "fcc",
            "piecesUsed": {k: inventory.get("pieces", {}).get(k, 0) - bag.get_count(k) 
                          for k in inventory.get("pieces", {})} if solved else inventory.get("pieces", {}),
            "placements": final_placements,
            "sid_state_sha256": "dfs_real_state",
            "sid_route_sha256": "dfs_real_route", 
            "sid_state_canon_sha256": sig,
        }
        yield {"t_ms": int((time.time()-t0)*1000), "type": "solution", "solution": sol}
        
        yield {"t_ms": int((time.time()-t0)*1000), "type": "done",
               "metrics": {"solutions": 1 if solved else 0, "nodes": nodes, "pruned": pruned,
                           "bestDepth": bestDepth, "smallMode": smallMode, "symGroup": symGroupSize, "seed": seed}}
