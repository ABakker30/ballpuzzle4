import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

def _run(cells, pieces, seed=123, max_results=5):
    with TemporaryDirectory() as d:
        d = Path(d)
        cpath = d / "c.json"
        container_data = {
            "name": "test_container",
            "lattice_type": "fcc",
            "coordinates": cells
        }
        cpath.write_text(json.dumps(container_data), encoding="utf-8")
        ev = d / "events.jsonl"
        sol = d / "solution.json"
        cmd = [
            sys.executable, "-m", "cli.solve", str(cpath),
            "--engine", "dfs",
            "--pieces", pieces,
            "--eventlog", str(ev),
            "--solution", str(sol),
            "--seed", str(seed),
            "--max-results", str(max_results),
        ]
        subprocess.check_call(cmd)
        return ev.read_text(encoding="utf-8"), json.loads(sol.read_text(encoding="utf-8"))

def test_symmetric_container_deduplication():
    # Symmetric container likely admits multiple rotated solutions; dedup should suppress duplicates
    # Use a small 2x2x1 pattern that your A piece can fit; allow a second piece that can't create a duplicate route.
    cells = [[0,0,0],[1,0,0],[0,1,0],[1,1,0]]
    log, sol = _run(cells, pieces="A=1", max_results=5)

    # Count unique canonical state signatures in the run
    seen_sids = set()
    solution_events = 0
    for line in log.splitlines():
        try:
            e = json.loads(line)
            if e.get("type") == "solution":
                solution_events += 1
                # canonical sid is in solution.json for the last solution; to be thorough, you could write each to file too.
        except Exception:
            pass

    # Only one solution event should be emitted thanks to canonical dedup
    assert solution_events == 1, f"Expected exactly 1 solution, got {solution_events}"

def test_multiple_solutions_different_pieces():
    # If you compose a tiny container that can be covered in two genuinely different ways
    # (not just rotations), make sure dedup does NOT suppress distinct canonical states.
    # This is a smoke test that asks for up to 2 results and accepts 1 or 2 depending on inventory/geometry.
    cells = [[0,0,0],[1,0,0],[2,0,0],[3,0,0]]
    log, sol = _run(cells, pieces="G=1", max_results=2)  # G is a 4-in-line in many A–Y sets
    # Just assert we didn't crash; stronger assertions can be added once your A–Y JSON is finalized.
    assert "sid_state_canon_sha256" in sol
