import json
import subprocess
import sys
from pathlib import Path

def _write_min_container(tmp_path: Path) -> Path:
    # Minimal FCC container: two adjacent cells
    cont = {"name": "test_container", "lattice_type": "fcc", "coordinates": [[0,0,0],[1,0,0]]}
    cpath = tmp_path / "c.json"
    cpath.write_text(json.dumps(cont), encoding="utf-8")
    return cpath

def test_cli_inventory_file(tmp_path):
    # Copy canned inventory into tmp
    inv_src = Path("tests/data/inventory.mini.json")
    inv_path = tmp_path / "inv.json"
    inv_path.write_text(inv_src.read_text(encoding="utf-8"), encoding="utf-8")

    cont_path = _write_min_container(tmp_path)
    sol_path = tmp_path / "solution.json"
    ev_path  = tmp_path / "events.jsonl"

    cmd = [
        sys.executable, "-m", "cli.solve", str(cont_path),
        "--engine", "current",
        "--inventory", str(inv_path),
        "--solution", str(sol_path),
        "--eventlog", str(ev_path),
    ]
    subprocess.check_call(cmd)

    sol = json.loads(sol_path.read_text(encoding="utf-8"))
    assert sol["lattice"] == "fcc"
    # Must match the inventory file exactly
    assert sol["piecesUsed"] == {"A": 2, "B": 1}

def test_cli_pieces_overrides_inventory(tmp_path):
    # Inventory file says A=2,B=1, but inline overrides to A=1,C=3
    inv_src = Path("tests/data/inventory.mini.json")
    inv_path = tmp_path / "inv.json"
    inv_path.write_text(inv_src.read_text(encoding="utf-8"), encoding="utf-8")

    cont_path = _write_min_container(tmp_path)
    sol_path = tmp_path / "solution.json"
    ev_path  = tmp_path / "events.jsonl"

    cmd = [
        sys.executable, "-m", "cli.solve", str(cont_path),
        "--engine", "current",
        "--inventory", str(inv_path),
        "--pieces", "A=1,C=3",              # should take precedence
        "--solution", str(sol_path),
        "--eventlog", str(ev_path),
    ]
    subprocess.check_call(cmd)

    sol = json.loads(sol_path.read_text(encoding="utf-8"))
    assert sol["piecesUsed"] == {"A": 1, "C": 3}
