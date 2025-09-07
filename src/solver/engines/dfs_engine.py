from typing import Iterator, List, Tuple, Dict, Any, Set
import time
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...solver.tt import OccMask, SeenMasks
from ...solver.symbreak import container_symmetry_group, anchor_rule_filter
from ...solver.heuristics import tie_shuffle
from ...solver.placement_gen import for_target, Placement
from ...solver.utils import first_empty_cell, support_contacts
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...pieces.inventory import PieceBag
from ...io.solution_sig import canonical_state_signature, extract_occupied_cells_from_placements

I3 = Tuple[int,int,int]

class DFSEngine(EngineProtocol):
    name = "dfs"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        import time
        t0 = time.time()
        seed = int(options.get("seed", 0))
        caps = options.get("caps", {}) or {}
        max_nodes = int(caps.get("maxNodes", 0))
        max_depth = int(caps.get("maxDepth", 0))
        max_results = int(options.get("max_results", 1))
        flags = options.get("flags", {}) or {}
        use_mrv = bool(flags.get("mrvPieces", False))
        use_support = bool(flags.get("supportBias", False))
        progress_every = int(options.get("progress_interval_ms", 0))
        last_tick_ms = 0

        cells_sorted: List[I3] = sorted(tuple(map(int,c)) for c in container["coordinates"])
        container_set = set(cells_sorted)
        symGroup = container_symmetry_group(cells_sorted)
        smallMode = len(cells_sorted) <= 32

        # init TT + occ + bag
        occ = OccMask(cells_sorted)
        TT = SeenMasks()
        # Piece bag based on inventory
        class Bag:
            def __init__(self, d: Dict[str,int]): self.d = dict(d)
            def to_dict(self): return dict(self.d)
            def dec(self, k): self.d[k] -= 1
            def inc(self, k): self.d[k] += 1
            def has(self, k): return self.d.get(k,0) > 0
        bag = Bag(inventory.get("pieces", {}))

        # placement stack for solution reconstruction
        stack: List[Placement] = []
        nodes = pruned = 0
        results = 0
        bestDepth = 0

        # occupied set for support metric
        occupied_set: Set[I3] = set()

        # piece library (load lazily via pieces.library if not prewired)
        from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
        lib = load_fcc_A_to_Y()

        def maybe_tick(current_depth):
            nonlocal last_tick_ms
            if not progress_every:
                return
            import time
            now = int((time.time()-t0)*1000)
            if now - last_tick_ms >= progress_every:
                last_tick_ms = now
                yield {"t_ms": now, "type":"tick",
                       "metrics":{"nodes": nodes, "pruned": pruned, "depth": current_depth,
                                  "bestDepth": bestDepth, "solutions": results}}

        def dfs(depth: int) -> bool:
            nonlocal nodes, pruned, bestDepth, results
            if max_nodes and nodes >= max_nodes:
                return False
            if max_depth and depth > max_depth:
                return False
            bestDepth = max(bestDepth, depth)

            # full cover
            if occ.popcount() == len(cells_sorted):
                # build solution
                final_cells = list(occupied_set)
                from ...io.solution_sig import canonical_state_signature
                sid_canon = canonical_state_signature(set(final_cells), symGroup)
                sol = {
                    "containerCidSha256": container["cid_sha256"],
                    "lattice": "fcc",
                    "piecesUsed": bag.to_dict(),
                    "placements": [{"piece": pl.piece, "ori": pl.ori_idx, "t": list(pl.t), "coordinates": [list(coord) for coord in pl.covered]} for pl in stack],
                    "sid_state_sha256": "dfs_state", "sid_route_sha256": "dfs_route",
                    "sid_state_canon_sha256": sid_canon,
                }
                yield {"t_ms": int((time.time()-t0)*1000), "type":"solution", "solution": sol}
                results += 1
                return results >= max_results

            target = first_empty_cell(occ, cells_sorted)
            if target is None:
                return False

            # Generate candidates
            cands = for_target(target, occ, bag, lib, container_set, seed, depth)

            # Optional MRV: approximate by counting number of placements per piece; prefer fewer first
            if use_mrv and cands:
                counts: Dict[str,int] = {}
                for pl in cands:
                    counts[pl.piece] = counts.get(pl.piece, 0) + 1
                cands.sort(key=lambda pl: (counts[pl.piece], pl.piece))

            # Optional support bias: prefer placements with more supports under gravity
            if use_support and cands:
                # Predict supports after adding this placement: current occupied plus covered
                def score(pl: Placement) -> int:
                    add = set(pl.covered)
                    return support_contacts(add, occupied_set | add)  # immediate supports count
                cands.sort(key=lambda pl: (-score(pl), pl.piece, pl.ori_idx))

            # Always apply seeded tie-shuffle last to break ties deterministically
            cands = tie_shuffle(cands, seed)

            # Depth-0 anchor filter remains (apply on (piece, covered) pairs)
            if depth == 0 and cands:
                packs = [(pl.piece, pl.covered) for pl in cands]
                kept = anchor_rule_filter(packs, target, lowest_piece=min(pl.piece for pl in cands), Rgroup=symGroup)
                keep_set = set((pid, cov) for pid, cov in kept)
                cands = [pl for pl in cands if (pl.piece, pl.covered) in keep_set]

            for pl in cands:
                if not bag.has(pl.piece):
                    continue
                # Apply
                old_mask = occ.mask
                bag.dec(pl.piece)
                occ.set_cells(pl.covered)
                occupied_set.update(pl.covered)
                nodes += 1
                if max_nodes and nodes > max_nodes:
                    # backtrack and stop
                    occupied_set.difference_update(pl.covered); occ.mask = old_mask; bag.inc(pl.piece)
                    return False
                if not TT.check_and_add(occ.mask):
                    pruned += 1
                    # backtrack
                    occupied_set.difference_update(pl.covered); occ.mask = old_mask; bag.inc(pl.piece)
                    continue
                stack.append(pl)
                # Emit tick events before recursion
                for ev in maybe_tick(depth):
                    yield ev
                # Recurse
                stop = False
                for ev in dfs(depth+1):
                    # bubble up solution events
                    yield ev
                    stop = True
                    # If we want multiple results, do not early-return; we captured the event upstream
                stack.pop()
                # backtrack
                occupied_set.difference_update(pl.covered)
                occ.mask = old_mask
                bag.inc(pl.piece)
                if stop and results >= max_results:
                    return True

            return False

        # Drive DFS
        for ev in dfs(0):
            yield ev

        # Done event
        yield {"t_ms": int((time.time()-t0)*1000), "type":"done",
               "metrics":{"solutions": results, "nodes": nodes, "pruned": pruned,
                          "bestDepth": bestDepth, "smallMode": smallMode,
                          "symGroup": len(symGroup), "seed": seed,
                          "maxNodes": max_nodes}}
