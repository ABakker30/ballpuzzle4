from typing import Iterator
import time
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent

class CurrentEngine(EngineProtocol):
    name = "current"
    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        # Deterministic stub: 3 ticks + 1 solution
        t0 = time.time()
        for i in range(3):
            yield {"t_ms": int((time.time()-t0)*1000), "type": "tick",
                   "metrics": {"nodes": (i+1)*1000, "pruned": (i+1)*700, "depth": i+10}}
            time.sleep(0.05)
        # Produce a trivial solution payload exercising the pipeline
        placements = []  # no real placements yet
        solution = {
            "containerCidSha256": container["cid_sha256"],
            "lattice": "fcc",
            "piecesUsed": inventory.get("pieces", {}),
            "placements": placements,
            "sid_state_sha256": "stub_state_hash",
            "sid_route_sha256": "stub_route_hash",
        }
        yield {"t_ms": int((time.time()-t0)*1000), "type": "solution", "solution": solution}
        yield {"t_ms": int((time.time()-t0)*1000), "type": "done", "metrics": {"solutions": 1}}
