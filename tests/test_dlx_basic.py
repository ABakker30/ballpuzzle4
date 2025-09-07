import json, subprocess, sys
from pathlib import Path
from tempfile import TemporaryDirectory

def _run(engine, cells, pieces="A=1", seed=123, max_results=1):
    with TemporaryDirectory() as d:
        d = Path(d)
        c = d/"c.json"; ev = d/"e.jsonl"; sol = d/"s.json"
        c.write_text(json.dumps({"name":"test_container","lattice_type":"fcc","coordinates":cells}), encoding="utf-8")
        cmd = [sys.executable,"-m","cli.solve",str(c),
               "--engine",engine,"--pieces",pieces,
               "--eventlog",str(ev),"--solution",str(sol),
               "--seed",str(seed),"--max-results",str(max_results)]
        subprocess.check_call(cmd)
        return ev.read_text(encoding="utf-8"), json.loads(sol.read_text(encoding="utf-8"))

def test_dlx_runs_on_tiny_4():
    cells = [[0,0,0],[1,0,0],[0,1,0],[1,1,0]]
    log, sol = _run("dlx", cells, pieces="A=1")
    assert "sid_state_canon_sha256" in sol
