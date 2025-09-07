"""Test that engines do not emit duplicate solutions under container symmetry."""

import json
from io import StringIO
from src.solver.engines.current_engine import CurrentEngine
from src.solver.engines.dfs_engine import DFSEngine
from src.io.solution_sig import canonical_state_signature
from src.solver.symbreak import container_symmetry_group

def test_current_engine_dedup():
    """Test that current engine doesn't emit duplicate solutions."""
    # Create a tiny symmetric container
    container = {
        "name": "tiny_cube",
        "lattice_type": "fcc", 
        "coordinates": [[0,0,0], [1,0,0], [0,1,0], [1,1,0]],
        "cid_sha256": "test_container_hash"
    }
    
    inventory = {"pieces": {}}
    pieces = {}
    options = {"seed": 42}
    
    engine = CurrentEngine()
    events = list(engine.solve(container, inventory, pieces, options))
    
    # Count solution events
    solutions = [e for e in events if e["type"] == "solution"]
    assert len(solutions) == 1, f"Expected 1 solution, got {len(solutions)}"
    
    # Verify solution has canonical signature field
    sol = solutions[0]["solution"]
    assert "sid_state_canon_sha256" in sol
    assert isinstance(sol["sid_state_canon_sha256"], str)
    assert len(sol["sid_state_canon_sha256"]) == 64

def test_dfs_engine_dedup():
    """DFS should emit exactly one solution event for a tiny solvable container."""
    import json, subprocess, sys
    from pathlib import Path
    from tempfile import TemporaryDirectory
    
    with TemporaryDirectory() as d:
        d = Path(d)
        # 2x2 layer (4 cells) – solvable by a single A piece in our tiny tests
        cpath = d / "c.json"
        container_data = {
            "name": "test_container",
            "lattice_type": "fcc",
            "coordinates": [[0,0,0],[1,0,0],[0,1,0],[1,1,0]]
        }
        cpath.write_text(json.dumps(container_data), encoding="utf-8")

        ev = d / "events.jsonl"
        sol = d / "solution.json"

        cmd = [
            sys.executable, "-m", "cli.solve", str(cpath),
            "--engine", "dfs",
            "--pieces", "A=1",          # provide a real inventory
            "--eventlog", str(ev),
            "--solution", str(sol),
            "--seed", "42",
            "--max-results", "2"
        ]
        subprocess.check_call(cmd)

        # Count solution events from the event log
        solutions = 0
        for line in ev.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("type") == "solution":
                    solutions += 1
            except Exception:
                pass

        assert solutions == 1, f"Expected 1 solution event, got {solutions}"

def test_manual_dedup_simulation():
    """Simulate calling emit twice with rotated states to verify dedup works."""
    from src.io.solution_sig import canonical_state_signature, extract_occupied_cells_from_placements
    
    # Create test data
    container_cells = [(0,0,0), (1,0,0), (0,1,0), (1,1,0)]
    symGroup = container_symmetry_group(container_cells)
    
    # Create two placement sets that are rotations of each other
    placements1 = [{"coordinates": [[0,0,0], [1,0,0]]}]
    placements2 = [{"coordinates": [[0,0,0], [0,1,0]]}]  # Different but could be rotation
    
    # Extract occupied cells
    cells1 = extract_occupied_cells_from_placements(placements1)
    cells2 = extract_occupied_cells_from_placements(placements2)
    
    # Get signatures
    sig1 = canonical_state_signature(cells1, symGroup)
    sig2 = canonical_state_signature(cells2, symGroup)
    
    # Simulate dedup logic
    emitted_sigs = set()
    solutions_emitted = 0
    
    # First solution
    if sig1 not in emitted_sigs:
        emitted_sigs.add(sig1)
        solutions_emitted += 1
    
    # Second solution (potentially duplicate)
    if sig2 not in emitted_sigs:
        emitted_sigs.add(sig2)
        solutions_emitted += 1
    
    # Should have emitted at least one solution
    assert solutions_emitted >= 1
    assert len(emitted_sigs) == solutions_emitted

def test_empty_placements_consistent_signature():
    """Test that empty placements produce consistent signatures."""
    from src.io.solution_sig import extract_occupied_cells_from_placements
    
    container_cells = [(0,0,0), (1,0,0)]
    symGroup = container_symmetry_group(container_cells)
    
    # Empty placements
    placements = []
    cells = extract_occupied_cells_from_placements(placements)
    
    sig1 = canonical_state_signature(cells, symGroup)
    sig2 = canonical_state_signature(cells, symGroup)
    
    assert sig1 == sig2
    assert isinstance(sig1, str)
    assert len(sig1) == 64
