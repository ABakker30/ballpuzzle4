import argparse, time, json, sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.solver.registry import get_engine
from src.io.container import load_container
from src.io.snapshot import open_eventlog, write_event
from src.io.solution import write_solution
from src.io.schema import load_schema
from jsonschema import validate

def _parse_inline_pieces(s: str) -> dict[str, int]:
    """
    Parse --pieces like: A=1,B=2,C=0
    Returns dict with non-negative ints. Ignores empty segments.
    Raises ValueError on bad tokens.
    """
    result: dict[str,int] = {}
    if not s:
        return result
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        if "=" not in tok:
            raise ValueError(f"Invalid token '{tok}'. Expected NAME=COUNT.")
        name, val = tok.split("=", 1)
        name = name.strip().upper()
        val = val.strip()
        if not (len(name) == 1 and name.isalpha()):
            raise ValueError(f"Invalid piece name '{name}'. Use single letters A..Z.")
        try:
            n = int(val)
        except Exception:
            raise ValueError(f"Invalid count '{val}' for piece '{name}'. Must be integer.")
        if n < 0:
            raise ValueError(f"Negative count '{n}' for piece '{name}'.")
        result[name] = n
    return result

def _load_inventory_json(path: str) -> dict[str,int]:
    """
    Read inventory JSON file:
      { "pieces": { "A":1, "B":2, ... } }
    Validates against inventory.schema.json and returns the inner dict.
    """
    schema = load_schema("inventory.schema.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    validate(instance=data, schema=schema)
    pieces = data.get("pieces", {})
    # Ensure ints
    clean = {k: int(v) for k, v in pieces.items()}
    return clean

def _resolve_inventory(args) -> dict[str,int]:
    """
    Precedence: --pieces (inline) > --inventory (file) > default all pieces (A-Y = 1 each).
    """
    if args.pieces:
        return _parse_inline_pieces(args.pieces)
    if args.inventory:
        return _load_inventory_json(args.inventory)
    # Default: all pieces A-Y available once each
    return {chr(ord('A') + i): 1 for i in range(25)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container", help="path to FCC container json")
    ap.add_argument("--engine", default="current", choices=["current","dfs","dlx","engine-c"])
    ap.add_argument("--eventlog", default="events.jsonl")
    ap.add_argument("--solution", default="solution.json")
    ap.add_argument("--seed", type=int, default=9000)
    ap.add_argument("--max-results", default="1")
    # NEW: simple caps option (nodes limit)
    ap.add_argument("--caps-max-nodes", type=int, default=0, help="max nodes before stopping (0 = unlimited)")
    ap.add_argument("--caps-max-depth", type=int, default=0, help="max DFS depth before stopping (0 = unlimited)")
    ap.add_argument("--caps-max-rows", type=int, default=0, help="max DLX rows to build (0 = unlimited)")
    ap.add_argument("--time-limit", type=int, default=0, help="max runtime in seconds before stopping (0 = unlimited)")
    ap.add_argument("--progress-interval-ms", type=int, default=0, help="emit tick events roughly every N milliseconds (0 = disabled)")
    # Optional heuristic toggles
    ap.add_argument("--mrv-pieces", action="store_true", help="enable MRV-based piece ordering")
    ap.add_argument("--support-bias", action="store_true", help="enable support-biased placement ordering")
    # NEW: inventory inputs
    ap.add_argument("--inventory", help="path to inventory JSON (with {\"pieces\":{...}})")
    ap.add_argument("--pieces", help="inline pieces, e.g. A=1,B=2 (takes precedence over --inventory)")
    args = ap.parse_args()

    container = load_container(args.container)

    # Resolve inventory
    try:
        pieces_used = _resolve_inventory(args)  # dict[str,int]
    except Exception as e:
        print(f"Error parsing inventory: {e}", file=sys.stderr)
        sys.exit(2)

    # For now we pass these through; solver engines can ignore them until M4+
    inventory = {"pieces": pieces_used}
    # Load piece library
    from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
    pieces = load_fcc_A_to_Y()

    engine = get_engine(args.engine)
    meta = {"engine": engine.name, "seed": args.seed,
            "flags": {"mrvPieces": bool(args.mrv_pieces), "supportBias": bool(args.support_bias)}}
    # Build options bundle
    options = {"seed": args.seed, "flags": meta["flags"], "caps": {"maxNodes": int(args.caps_max_nodes), "maxDepth": int(args.caps_max_depth), "maxRows": int(args.caps_max_rows)}, "max_results": int(args.max_results), "progress_interval_ms": int(args.progress_interval_ms), "time_limit_seconds": int(args.time_limit) if args.time_limit > 0 else None}

    emitted_solution = False

    # Schema validation setup
    from src.io.schema import load_schema
    from jsonschema import validate as _validate
    _event_schema = load_schema("snapshot.schema.json")
    
    def _write(ev, fp):
        ev = {"v": 1, **ev}
        _validate(instance=ev, schema=_event_schema)
        write_event(ev, fp)

    with open_eventlog(args.eventlog) as fp:
        import time
        t0 = time.time()
        for ev in engine.solve(container, inventory, pieces, options):
            ev.setdefault("t_ms", int((time.time()-t0)*1000))
            _write(ev, fp)
            if ev["type"] == "solution":
                # Ensure piecesUsed is included exactly as resolved
                sol = dict(ev["solution"])
                if "piecesUsed" not in sol:
                    sol["piecesUsed"] = pieces_used
                write_solution(args.solution, sol, meta, pieces_used)
                emitted_solution = True

        # If the engine emitted no 'solution' event, write a stub to avoid missing file
        if not emitted_solution:
            from src.io.solution_sig import canonical_state_signature
            from src.solver.symbreak import container_symmetry_group
            cells = sorted(tuple(map(int,c)) for c in container["coordinates"])
            symGroup = container_symmetry_group(cells)
            stub = {"containerCidSha256": container["cid_sha256"], "lattice":"fcc",
                    "piecesUsed": pieces_used, "placements": [],
                    "sid_state_sha256":"no_solution","sid_route_sha256":"no_solution",
                    "sid_state_canon_sha256": canonical_state_signature(set(), symGroup)}
            write_solution(args.solution, stub, meta, pieces_used)

if __name__ == "__main__":
    main()
