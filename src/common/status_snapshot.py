# Shared types + JSON-safe dict builder for snapshots
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Optional, Literal
import time, os, json, tempfile

EngineName = Literal["dfs", "dlx", "c"]

@dataclass
class StackItem:
    piece: int      # index in canonical piece table
    orient: int     # index in that piece's orientation table
    i: int          # FCC lattice integer coords (anchor cell)
    j: int
    k: int

@dataclass
class ContainerInfo:
    cid: str
    cells: int

@dataclass
class Snapshot:
    v: int
    ts_ms: int
    engine: EngineName
    run_id: str
    container: ContainerInfo
    k: Optional[int]
    nodes: int
    pruned: int
    depth: int
    best_depth: Optional[int]
    solutions: int
    elapsed_ms: int
    stack: List[StackItem]
    stack_truncated: bool = False
    hash_container_cid: Optional[str] = None
    hash_solution_sid: Optional[str] = None
    phase: Optional[str] = None  # "init"|"search"|"verifying"|"done"|None

    def to_json_str(self) -> str:
        # Ensure integers remain integers; do not serialize floats
        d = asdict(self)
        return json.dumps(d, separators=(",", ":"), ensure_ascii=False)

def now_ms() -> int:
    return int(time.time() * 1000)

def atomic_write_json(path: str, json_str: str) -> None:
    """Atomic replace: write temp then rename."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".status_", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json_str)
        # On Windows, replace is atomic for same-volume renames in recent Python
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass
