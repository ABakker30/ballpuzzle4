import json, subprocess, sys
from pathlib import Path
from tempfile import TemporaryDirectory

def test_perf_smoke_medium_container_nodes_cap():
    """Test performance smoke test with medium container and node cap."""
    # a simple 12-cell rectangle (adjust cells as needed for your A–Y library)
    cells = [[x,0,0] for x in range(6)] + [[x,1,0] for x in range(6)]
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
               "--engine","dfs","--pieces","A=2,D=1", # small inventory
               "--eventlog",str(ev),"--solution",str(sol),
               "--seed","123","--caps-max-nodes","50000","--max-results","1"]
        subprocess.check_call(cmd)
        # assert done event exists
        lines = ev.read_text(encoding="utf-8").splitlines()
        assert any('"type": "done"' in ln for ln in lines)
