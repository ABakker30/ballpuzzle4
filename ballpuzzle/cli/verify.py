import sys, json
from pathlib import Path
from src.io.container import load_container
from src.io.solution_sig import canonical_state_signature
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
from src.solver.symbreak import container_symmetry_group

def main():
    if len(sys.argv) != 3:
        print("usage: python -m cli.verify solution.json container.json", file=sys.stderr)
        sys.exit(1)

    sol_path = Path(sys.argv[1]); cont_path = Path(sys.argv[2])
    sol = json.loads(sol_path.read_text(encoding="utf-8"))
    
    # Use v1.0 container loader with validation
    try:
        container = load_container(str(cont_path))
    except ValueError as e:
        print(f"Container validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to load container: {e}", file=sys.stderr)
        sys.exit(1)
    
    container_cells = {tuple(map(int,c)) for c in container["coordinates"]}
    lib = load_fcc_A_to_Y()

    covered = set()
    for pl in sol.get("placements", []):
        pid = pl["piece"]; ori = pl["ori"]; dx,dy,dz = pl["t"]
        pdef = lib.get(pid)
        if not pdef:
            print(f"unknown piece {pid}"); sys.exit(2)
        try:
            orient = pdef.orientations[ori]
        except IndexError:
            print(f"invalid orientation index {ori} for piece {pid}"); sys.exit(2)
        cov = [(u[0]+dx,u[1]+dy,u[2]+dz) for u in orient]
        for c in cov:
            if c not in container_cells:
                print(f"cell {c} not in container"); sys.exit(2)
            if c in covered:
                print(f"overlap at {c}"); sys.exit(2)
            covered.add(c)

    if covered != container_cells:
        missing = container_cells - covered
        extra = covered - container_cells
        if missing: print(f"missing cells: {sorted(missing)}")
        if extra: print(f"extra cells: {sorted(extra)}")
        sys.exit(2)

    # Recompute canonical signature
    cells_sorted = sorted(tuple(map(int,c)) for c in container["coordinates"])
    symGroup = container_symmetry_group(cells_sorted)
    recomputed_sid = canonical_state_signature(covered, symGroup)
    stored_sid = sol.get("sid_state_canon_sha256")
    if stored_sid != recomputed_sid:
        print("canonical sid mismatch")
        print(f"stored: {stored_sid}")
        print(f"recomputed: {recomputed_sid}")
        sys.exit(2)

    print("solution verified ok")
    sys.exit(0)

if __name__ == "__main__":
    main()
