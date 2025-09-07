import json, subprocess, sys
from pathlib import Path
from tempfile import TemporaryDirectory

def run_cli(cells, pieces="A=2,D=1", max_nodes=100000, max_depth=50):
    with TemporaryDirectory() as d:
        d = Path(d)
        cpath = d/"c.json"
        container_data = {
            "name": "test_container",
            "lattice_type": "fcc",
            "coordinates": cells
        }
        cpath.write_text(json.dumps(container_data), encoding="utf-8")
        ev = d/"e.jsonl"; sol = d/"s.json"
        cmd = [sys.executable,"-m","cli.solve",str(cpath),
               "--engine","dfs","--pieces",pieces,
               "--eventlog",str(ev),"--solution",str(sol),
               "--seed","123",
               "--caps-max-nodes",str(max_nodes),
               "--caps-max-depth",str(max_depth),
               "--max-results","1"]
        subprocess.check_call(cmd)
        return ev.read_text(encoding="utf-8")

def test_medium_container_20cells():
    cells = json.load(open("tests/data/containers/tiny_20.fcc.json"))["coordinates"]
    log = run_cli(cells)
    assert any('"type": "done"' in ln for ln in log.splitlines())

def test_medium_container_24cells():
    cells = json.load(open("tests/data/containers/tiny_24.fcc.json"))["coordinates"]
    log = run_cli(cells, max_nodes=200000, max_depth=60)
    assert any('"type": "done"' in ln for ln in log.splitlines())

def test_medium_container_32cells():
    cells = json.load(open("tests/data/containers/tiny_32.fcc.json"))["coordinates"]
    log = run_cli(cells, max_nodes=500000, max_depth=80)
    assert any('"type": "done"' in ln for ln in log.splitlines())
