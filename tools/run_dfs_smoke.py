# tools/run_dfs_smoke.py
import json, sys, time
from src.solver.engines.dfs_engine import DFSEngine  # adjust import to your path
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y

def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def print_solution(sol):
    used = sol["piecesUsed"]
    print(f"piecesUsed: {used}")
    print(f"placements: {len(sol['placements'])}")
    for i, pl in enumerate(sol["placements"][:6]):
        print(f"  [{i}] {pl['piece']} ori={pl['ori']} t={tuple(pl['t'])}")

def main(container_path, inventory_json=None):
    container = load_json(container_path)
    if inventory_json:
        inventory = load_json(inventory_json)
    else:
        # default: try 4 random letters summing to N/4 if none provided
        # Handle both "coordinates" and "cells" formats
        coords = container.get("coordinates") or container.get("cells", [])
        pieces_needed = len(coords) // 4
        inventory = {"pieces": {}}
        # simple baseline that often works on small shapes:
        for k in ["A","E","T","L","N","P","U","V","W","X","Y"]:
            if pieces_needed <= 0: break
            take = min(1, pieces_needed)
            inventory["pieces"][k] = inventory["pieces"].get(k, 0) + take
            pieces_needed -= take

    opts = {
        "seed": 0,
        "time_limit": 10.0,
        "max_results": 3,
        "restart_interval_s": 2.0,
        "restart_nodes": 50_000,
        "pivot_cycle": True,
        "mrv_window": 12,
        "hole_pruning": "none",      # start permissive; tighten later
        "assert_io": True,           # enable debug output
    }

    eng = DFSEngine()
    t0 = time.time()
    found = 0
    for ev in eng.solve(container, inventory, pieces=None, options=opts):
        if ev["type"] == "solution":
            found += 1
            print(f"\n--- SOLUTION #{found} @ {ev['t_ms']} ms ---")
            print_solution(ev["solution"])
        elif ev["type"] == "done":
            print("\n--- DONE ---")
            print(ev["metrics"])
    print(f"\nElapsed: {time.time()-t0:.3f}s")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tools.run_dfs_smoke <container.json> [inventory.json]")
        sys.exit(1)
    main(*sys.argv[1:])
