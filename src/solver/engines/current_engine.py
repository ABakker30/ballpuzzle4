from typing import Iterator
import time
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...solver.symbreak import container_symmetry_group
from ...solver.tt import SeenMasks
from ...solver.heuristics import tie_shuffle

class CurrentEngine(EngineProtocol):
    name = "current"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        t0 = time.time()
        cells = [tuple(map(int, c)) for c in container["coordinates"]]
        smallMode = len(cells) <= 32
        symGroup = len(container_symmetry_group(cells))
        seed = int(options.get("seed", 0))
        tt = SeenMasks()

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
                    "symGroup": symGroup,
                    "seed": seed,
                    "ttEnabled": True,
                    "probe": probe_shuffled,
                }
            }
            time.sleep(0.02)

        solution = {
            "containerCidSha256": container["cid_sha256"],
            "lattice": "fcc",
            "piecesUsed": inventory.get("pieces", {}),
            "placements": [],
            "sid_state_sha256": "stub_state_hash",
            "sid_route_sha256": "stub_route_hash",
        }
        yield {"t_ms": int((time.time()-t0)*1000), "type": "solution", "solution": solution}
        yield {"t_ms": int((time.time()-t0)*1000), "type": "done",
               "metrics": {"solutions": 1, "smallMode": smallMode, "symGroup": symGroup, "seed": seed, "ttEnabled": True}}
