import json
from typing import Dict, Any

def write_solution(path: str, solution: Dict[str, Any], meta: Dict[str, Any], pieces_used: Dict[str, int]) -> None:
    payload = {
        "version": 1,
        **solution,
        "piecesUsed": pieces_used,
        "mode": meta.get("mode", "solver"),
        "solver": {
            "engine": meta["engine"],
            "seed": meta.get("seed"),
            "flags": meta.get("flags", {}),
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
