# Status Snapshot v2 - cells per placement + instance IDs
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Optional, Literal
import time, os, json, tempfile

EngineName = Literal["dfs", "dlx", "c"]

@dataclass
class Cell:
    i: int
    j: int
    k: int

@dataclass
class PlacedPiece:
    instance_id: int
    piece_type: int
    piece_label: str
    cells: List[Cell]

@dataclass
class Metrics:
    nodes: int
    pruned: int
    depth: int
    solutions: int
    elapsed_ms: int
    best_depth: Optional[int] = None

@dataclass
class ContainerInfo:
    cid: str
    cells: int

@dataclass
class StatusV2:
    version: int
    ts_ms: int
    engine: EngineName
    phase: str
    run_id: str
    container: ContainerInfo
    metrics: Metrics
    stack: List[PlacedPiece]
    stack_truncated: bool = False

    def to_json_str(self) -> str:
        d = asdict(self)
        return json.dumps(d, separators=(",", ":"), ensure_ascii=False)

# Legacy v1 types for backward compatibility during transition
@dataclass
class StackItem:
    piece: int
    orient: int
    i: int
    j: int
    k: int

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
    phase: Optional[str] = None

    def to_json_str(self) -> str:
        d = asdict(self)
        return json.dumps(d, separators=(",", ":"), ensure_ascii=False)

# Piece definitions for v2 cell expansion
PIECE_DEFINITIONS = {
    0: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]],  # A
    1: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],  # B
    2: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 0]],  # C
    3: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [2, 1, 0]],  # D
    4: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 1]],  # E
    5: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 0, 1]],  # F
    6: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]],  # G
    7: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 1, 1]],  # H
    8: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 1]],  # I
    9: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [2, 0, 0]],  # J
    10: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 1, 1]], # K
    11: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 1]], # L
    12: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 0]], # M
    13: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 0, 1]], # N
    14: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 1]], # O
    15: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 2]], # P
    16: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [2, 1, 0]], # Q
    17: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 0, 1]], # R
    18: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [2, 0, 0]], # S
    19: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [2, 1, 0]], # T
    20: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 1]], # U
    21: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], # V
    22: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 2]], # W
    23: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 1]], # X
    24: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 2, 0]], # Y
}

def label_for_piece(piece_type: int) -> str:
    """Convert piece type to label (A-Y, then wrap)"""
    if 0 <= piece_type <= 24:
        return chr(65 + piece_type)  # A=65, B=66, etc.
    return chr(65 + (piece_type % 25))  # Wrap after Y

def expand_piece_to_cells(piece_type: int, anchor_i: int, anchor_j: int, anchor_k: int) -> List[Cell]:
    """Expand a piece placement to its 4 constituent cells"""
    if piece_type not in PIECE_DEFINITIONS:
        return []
    
    cells = []
    for offset in PIECE_DEFINITIONS[piece_type]:
        cell_i = anchor_i + offset[0]
        cell_j = anchor_j + offset[1]
        cell_k = anchor_k + offset[2]
        cells.append(Cell(i=cell_i, j=cell_j, k=cell_k))
    
    return cells

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
