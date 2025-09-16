import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

def run_cli(container_cells, pieces_inline="A=1", seed=123, max_results=1):
    """Run CLI solve command and return solution and eventlog."""
    with TemporaryDirectory() as d:
        cpath = Path(d) / "c.json"
        container_data = {
            "name": "test_container",
            "lattice_type": "fcc",
            "coordinates": container_cells
        }
        cpath.write_text(json.dumps(container_data), encoding="utf-8")
        ev = Path(d) / "e.jsonl"
        sol = Path(d) / "s.json"
        cmd = [
            sys.executable, "-m", "cli.solve", str(cpath),
            "--engine", "dfs", "--pieces", pieces_inline,
            "--eventlog", str(ev), "--solution", str(sol), "--seed", str(seed),
            "--max-results", str(max_results)
        ]
        subprocess.check_call(cmd)
        
        # Now solution file should always exist (CLI writes stub when no solution)
        s = json.loads(sol.read_text(encoding="utf-8"))
        return s, ev.read_text(encoding="utf-8")

def test_finds_real_solution_on_tiny_4():
    """Test that DFS finds a real solution on 4-cell container matching piece A."""
    cells = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]  # matches piece A exactly
    sol, log = run_cli(cells, pieces_inline="A=1")
    
    assert sol["placements"], "expected non-empty placements"
    assert len(sol["placements"]) == 1, "expected exactly one placement for piece A"
    
    # Verify placement structure
    placement = sol["placements"][0]
    assert placement["piece"] == "A"
    assert "ori" in placement
    assert "t" in placement
    assert "coordinates" in placement
    
    # Verify all container cells are covered
    covered_cells = set(tuple(coord) for coord in placement["coordinates"])
    expected_cells = set(tuple(cell) for cell in cells)
    assert covered_cells == expected_cells, f"placement covers {covered_cells}, expected {expected_cells}"
    
    # Verify canonical signature exists
    assert "sid_state_canon_sha256" in sol
    assert sol["sid_state_canon_sha256"] != ""

def test_finds_real_solution_on_tiny_8():
    """Test that DFS finds a real solution on 8-cell container with two pieces."""
    # 8-cell container that can be solved with 2 pieces of 4 cells each
    cells = [
        [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],  # first 4-cell block
        [2, 0, 0], [3, 0, 0], [2, 1, 0], [3, 1, 0]   # second 4-cell block
    ]
    sol, log = run_cli(cells, pieces_inline="A=2")  # 2 pieces A should work
    
    assert sol["placements"], "expected non-empty placements"
    assert len(sol["placements"]) == 2, "expected exactly two placements for 2 pieces A"
    
    # Verify all container cells are covered by placements
    covered_cells = set()
    for placement in sol["placements"]:
        for coord in placement["coordinates"]:
            covered_cells.add(tuple(coord))
    
    expected_cells = set(tuple(cell) for cell in cells)
    assert covered_cells == expected_cells, f"placements cover {covered_cells}, expected {expected_cells}"
    
    # Verify no overlaps
    all_coords = []
    for placement in sol["placements"]:
        all_coords.extend(tuple(coord) for coord in placement["coordinates"])
    assert len(all_coords) == len(set(all_coords)), "placements should not overlap"

def test_deterministic_first_solution():
    """Test that DFS produces deterministic results with same seed."""
    cells = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
    s1, _ = run_cli(cells, seed=42)
    s2, _ = run_cli(cells, seed=42)
    
    assert s1["placements"] == s2["placements"], "same seed should produce identical solutions"

def test_no_solution_insufficient_inventory():
    """Test that DFS correctly reports no solution when inventory is insufficient."""
    cells = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
    sol, log = run_cli(cells, pieces_inline="B=1")  # B doesn't match this shape
    
    # Should find no solution
    assert not sol["placements"], "expected empty placements when no solution exists"

def test_respects_inventory_limits():
    """Test that DFS respects piece inventory limits."""
    # 8-cell container that would need 2 pieces A, but only give 1
    cells = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [2, 0, 0], [3, 0, 0], [2, 1, 0], [3, 1, 0]]
    sol, log = run_cli(cells, pieces_inline="A=1")  # Only 1 A piece for 8 cells
    
    # Should find no solution since 1 piece A can't fill 8 cells
    assert not sol["placements"], "expected no solution when inventory insufficient"
