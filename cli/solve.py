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
    Precedence: --pieces (inline) > --inventory (file) > {}.
    """
    if args.pieces:
        return _parse_inline_pieces(args.pieces)
    if args.inventory:
        return _load_inventory_json(args.inventory)
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("container", help="path to FCC container json")
    ap.add_argument("--engine", default="current", choices=["current","dfs"])
    ap.add_argument("--eventlog", default="events.jsonl")
    ap.add_argument("--solution", default="solution.json")
    ap.add_argument("--seed", type=int, default=9000)
    ap.add_argument("--max-results", type=int, default=1, help="maximum number of solutions to find")
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
    pieces = {}  # (your piece library wiring comes later)

    engine = get_engine(args.engine)
    meta = {"engine": engine.name, "seed": args.seed, "flags": {}}

    emitted_solution = False

    with open_eventlog(args.eventlog) as fp:
        t0 = time.time()
        options = {"seed": args.seed, "max_results": args.max_results, "flags": {}}
        for ev in engine.solve(container, inventory, pieces, options):
            ev.setdefault("t_ms", int((time.time()-t0)*1000))
            write_event(ev, fp)
            if ev["type"] == "solution":
                # Ensure piecesUsed is included exactly as resolved
                sol = dict(ev["solution"])
                if "piecesUsed" not in sol:
                    sol["piecesUsed"] = pieces_used
                write_solution(args.solution, sol, meta, pieces_used)
                emitted_solution = True

        # If the engine emitted no 'solution' event, write a stub to avoid missing file
        if not emitted_solution:
            # minimal "no-solution" payload
            stub = {
                "containerCidSha256": container.get("cid_sha256", "unknown"),
                "lattice": "fcc",
                "piecesUsed": pieces_used,
                "placements": [],
                "sid_state_sha256": "no_solution",
                "sid_route_sha256": "no_solution",
                "sid_state_canon_sha256": "no_solution",
            }
            write_solution(args.solution, stub, meta, pieces_used)

if __name__ == "__main__":
    main()
