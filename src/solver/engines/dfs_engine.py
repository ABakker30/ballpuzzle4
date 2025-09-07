from typing import Iterator
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent

class DFSEngine(EngineProtocol):
    name = "dfs"
    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        # Placeholder identical shape to current; distinct name for plumbing tests.
        yield {"t_ms": 0, "type": "tick", "metrics": {"nodes": 0, "pruned": 0, "depth": 0}}
        yield {"t_ms": 1, "type": "done", "metrics": {"solutions": 0}}
