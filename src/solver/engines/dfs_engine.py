from typing import Iterator, List, Tuple, Dict, Any, Set
import time
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...solver.tt import OccMask, SeenMasks
from ...solver.symbreak import container_symmetry_group, anchor_rule_filter
from ...solver.heuristics import tie_shuffle
from ...io.solution_sig import canonical_state_signature, extract_occupied_cells_from_placements

I3 = Tuple[int,int,int]

class DFSEngine(EngineProtocol):
    name = "dfs"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        """
        Minimal DFS scaffold:
        - order cells canonically (sorted)
        - depth-first over cells with fake 'placements' (each 'placement' fills one cell)
        - use TT to prune duplicate masks
        - at depth 0, apply anchor_rule_filter to placement candidates (synthetic)
        - tie-shuffle candidate order with seed
        Emits one synthetic solution to prove end-to-end path.
        """
        t0 = time.time()
        seed = int(options.get("seed", 0))
        cells: List[I3] = sorted(tuple(map(int,c)) for c in container["coordinates"])
        smallMode = len(cells) <= 32
        symGroup = container_symmetry_group(cells)
        symGroupSize = len(symGroup)
        tt = SeenMasks()
        occ = OccMask(cells)
        
        # Track emitted solution signatures for deduplication
        emitted_sigs: Set[str] = set()

        # synthetic "candidate generator": choose next index and offer up to 3 trivial placements:
        def candidates_at(depth: int) -> List[List[I3]]:
            # Pretend we can place exactly one new cell per 'placement'
            # Offer the next cell plus 0-2 duplicates (to exercise tie-shuffle/TT)
            next_idx = depth
            if next_idx >= len(cells): return []
            c = cells[next_idx]
            return [[c], [c], [c]]  # duplicates on purpose; TT will prune revisits

        nodes = pruned = 0
        bestDepth = 0
        solution_emitted = False

        def dfs(depth: int):
            nonlocal nodes, pruned, bestDepth, solution_emitted
            bestDepth = max(bestDepth, depth)

            if depth == len(cells):
                # build a trivial solution structure
                return True

            cands = candidates_at(depth)
            # depth 0: anchor filter demo (synthetic) — require next cell equals min cell
            if depth == 0:
                min_cell = min(cells)
                # we emulate the anchor_rule_filter API: (pid, atoms) — here pid="A", atoms=tuple(cells chosen so far + [candidate])
                pack = [("A", tuple(sorted([min_cell]))),
                        ("A", tuple(sorted([min_cell]))),
                        ("A", tuple(sorted([min_cell])))]
                # it will deduplicate; keep count parity with cands
                filtered = anchor_rule_filter(pack, min_cell, "A", symGroup)
                # if it filtered down to 1, trim candidates as well
                if len(filtered) == 1 and len(cands) > 1:
                    cands = cands[:1]

            # tie-shuffle candidate order (deterministic under seed)
            cands = tie_shuffle(cands, seed)

            for group in cands:
                # mark occupancy for these cells
                old_mask = occ.mask
                occ.set_cells(group)
                nodes += 1
                if not tt.check_and_add(occ.mask):
                    pruned += 1
                    occ.mask = old_mask
                    continue

                if dfs(depth+1):
                    return True  # stop at first synthetic solution

                # backtrack
                occ.mask = old_mask

            return False

        # drive dfs with periodic ticks
        solved = dfs(0)

        # Create a synthetic solution with empty placements for testing
        placements = []
        occupied_cells = extract_occupied_cells_from_placements(placements)
        
        # Compute canonical signature
        sig = canonical_state_signature(occupied_cells, symGroup)
        
        # Check for duplicate before emitting
        if sig not in emitted_sigs:
            emitted_sigs.add(sig)
            sol = {
                "containerCidSha256": container["cid_sha256"],
                "lattice": "fcc",
                "piecesUsed": inventory.get("pieces", {}),
                "placements": placements,
                "sid_state_sha256": "dfs_stub_state",
                "sid_route_sha256": "dfs_stub_route",
                "sid_state_canon_sha256": sig,
            }
            yield {"t_ms": int((time.time()-t0)*1000), "type": "solution", "solution": sol}
        
        yield {"t_ms": int((time.time()-t0)*1000), "type": "done",
               "metrics": {"solutions": len(emitted_sigs), "nodes": nodes, "pruned": pruned,
                           "bestDepth": bestDepth, "smallMode": smallMode, "symGroup": symGroupSize, "seed": seed}}
