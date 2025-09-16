import argparse, time, json, sys
from pathlib import Path
import os

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
    ap.add_argument("--engine", choices=["dfs", "dlx"], default="dfs", help="solver engine")
    ap.add_argument("--eventlog", default="events.jsonl")
    ap.add_argument("--solution", default="solutions/solution.json")
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
    ap.add_argument("--hole4", action="store_true", help="enable hole4 detection pruning (disconnected void detection)")
    ap.add_argument("--piece-rotation-interval", type=float, default=5.0, help="seconds between piece rotation for diversified search (DFS engine only)")
    # Enhanced DFS engine options
    ap.add_argument("--restart-interval-s", type=float, default=30.0, help="DFS restart interval in seconds (default: 30.0)")
    ap.add_argument("--restart-nodes", type=int, default=100000, help="DFS restart after N nodes explored (default: 100000)")
    ap.add_argument("--pivot-cycle", action="store_true", help="enable pivot cycling over start piece and orientation")
    ap.add_argument("--mrv-window", type=int, default=0, help="MRV window size for target cell selection (0=disabled, default: 0)")
    ap.add_argument("--hole-pruning", choices=["none", "single_component", "lt4"], default="none", help="hole pruning mode (default: none)")
    # Status JSON emission
    ap.add_argument("--status-json", type=str, default=None, help="Path to write periodic status snapshot JSON (includes placement stack).")
    ap.add_argument("--status-interval-ms", type=int, default=1000, help="Interval for status emission in milliseconds (>=50).")
    ap.add_argument("--status-max-stack", type=int, default=512, help="Safety cap for serialized stack length; emits stack_truncated=true if capped.")
    ap.add_argument("--status-phase", type=str, default=None, help="Optional phase label to include in snapshot (init|search|verifying|done).")
    # NEW: inventory inputs
    ap.add_argument("--inventory", help="path to inventory JSON (with {\"pieces\":{...}})")
    ap.add_argument("--pieces", help="inline pieces, e.g. A=1,B=2 (takes precedence over --inventory)")
    args = ap.parse_args()

    # Ensure solutions directory exists
    solution_path = Path(args.solution)
    solution_path.parent.mkdir(parents=True, exist_ok=True)

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
    options = {"seed": args.seed, "flags": meta["flags"], "caps": {"maxNodes": int(args.caps_max_nodes), "maxDepth": int(args.caps_max_depth), "maxRows": int(args.caps_max_rows)}, "max_results": int(args.max_results), "progress_interval_ms": int(args.progress_interval_ms), "time_limit": int(args.time_limit) if args.time_limit > 0 else 0, "hole4": bool(args.hole4), "piece_rotation_interval": float(args.piece_rotation_interval), "restart_interval_s": float(args.restart_interval_s), "restart_nodes": int(args.restart_nodes), "pivot_cycle": bool(args.pivot_cycle), "mrv_window": int(args.mrv_window), "hole_pruning": args.hole_pruning, "status_json": args.status_json, "status_interval_ms": int(args.status_interval_ms), "status_max_stack": int(args.status_max_stack), "status_phase": args.status_phase}

    emitted_solution = False
    solution_count = 0

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
                
                # Generate unique filename for multiple solutions
                solution_count += 1
                if int(args.max_results) > 1:
                    # For multiple solutions, include container name and solution number
                    solution_path = Path(args.solution)
                    container_path = Path(args.container)
                    container_name = container_path.stem.replace(' ', '_')  # Replace spaces with underscores
                    
                    base_name = solution_path.stem
                    extension = solution_path.suffix
                    numbered_filename = f"{container_name}_{base_name}_{solution_count:03d}{extension}"
                    numbered_path = solution_path.parent / numbered_filename
                    write_solution(str(numbered_path), sol, meta, pieces_used)
                else:
                    # Single solution, include container name
                    solution_path = Path(args.solution)
                    container_path = Path(args.container)
                    container_name = container_path.stem.replace(' ', '_')  # Replace spaces with underscores
                    
                    base_name = solution_path.stem
                    extension = solution_path.suffix
                    single_filename = f"{container_name}_{base_name}{extension}"
                    single_path = solution_path.parent / single_filename
                    write_solution(str(single_path), sol, meta, pieces_used)
                
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
            
            # Include container name in no-solution stub filename too
            solution_path = Path(args.solution)
            container_path = Path(args.container)
            container_name = container_path.stem.replace(' ', '_')
            
            base_name = solution_path.stem
            extension = solution_path.suffix
            stub_filename = f"{container_name}_{base_name}_no_solution{extension}"
            stub_path = solution_path.parent / stub_filename
            write_solution(str(stub_path), stub, meta, pieces_used)

if __name__ == "__main__":
    main()
