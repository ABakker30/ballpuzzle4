from typing import Iterator, Set
import time
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...solver.symbreak import container_symmetry_group
from ...solver.tt import SeenMasks
from ...solver.heuristics import tie_shuffle
from ...io.solution_sig import canonical_state_signature, extract_occupied_cells_from_placements

class CurrentEngine(EngineProtocol):
    name = "current"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        t0 = time.time()
        cells = [tuple(map(int, c)) for c in container["coordinates"]]
        smallMode = len(cells) <= 32
        symGroup = container_symmetry_group(cells)
        symGroupSize = len(symGroup)
        seed = int(options.get("seed", 0))
        tt = SeenMasks()
        
        # Track emitted solution signatures for deduplication
        emitted_sigs: Set[str] = set()

        # prove deterministic tie-shuffle without affecting behavior:
        probe = list(range(5))
        probe_shuffled = tie_shuffle(probe, seed)  # just for logging

        # 3 ticks + 1 solution + done (same as before, add fields)
        for i in range(3):
            yield {
                "t_ms": int((time.time()-t0)*1000),
                "type": "tick",
                "metrics": {
                    "nodes": (i+1)*1000,
                    "pruned": (i+1)*700,
                    "depth": i+10,
                    "smallMode": smallMode,
                    "symGroup": symGroupSize,
                    "seed": seed,
                    "ttEnabled": True,
                    "probe": probe_shuffled,
                }
            }
            time.sleep(0.02)

        # Create a stub solution with empty placements for testing
        placements = []
        occupied_cells = extract_occupied_cells_from_placements(placements)
        
        # Compute canonical signature
        sig = canonical_state_signature(occupied_cells, symGroup)
        
        # Check for duplicate before emitting
        if sig not in emitted_sigs:
            emitted_sigs.add(sig)
            solution = {
                "containerCidSha256": container["cid_sha256"],
                "lattice": "fcc",
                "piecesUsed": inventory.get("pieces", {}),
                "placements": placements,
                "sid_state_sha256": "stub_state_hash",
                "sid_route_sha256": "stub_route_hash",
                "sid_state_canon_sha256": sig,
            }
            yield {"t_ms": int((time.time()-t0)*1000), "type": "solution", "solution": solution}
        
        yield {"t_ms": int((time.time()-t0)*1000), "type": "done",
               "metrics": {"solutions": len(emitted_sigs), "smallMode": smallMode, "symGroup": symGroupSize, "seed": seed, "ttEnabled": True}}
