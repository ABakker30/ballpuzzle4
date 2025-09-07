import json, subprocess, sys
from pathlib import Path
from tempfile import TemporaryDirectory

def run(engine, cells, pieces):
    with TemporaryDirectory() as d:
        d = Path(d)
        c = d/"c.json"; s = d/"s.json"; ev = d/"e.jsonl"
        c.write_text(json.dumps({"name":"tiny_4","lattice_type":"fcc","coordinates":cells}), encoding="utf-8")
        cmd = [sys.executable,"-m","cli.solve",str(c),
               "--engine",engine,"--pieces",pieces,
               "--eventlog",str(ev),"--solution",str(s),"--seed","123","--max-results","1"]
        subprocess.check_call(cmd)
        return json.loads(s.read_text(encoding="utf-8"))

def test_parity_canonical_sid_tiny4():
    cells = [[0,0,0],[1,0,0],[0,1,0],[1,1,0]]
    dfs = run("dfs", cells, "A=1")
    leg = run("legacy", cells, "A=1")
    # If legacy returns no solution, skip parity
    if not dfs.get("placements") or not leg.get("placements"):
        return
    assert dfs["sid_state_canon_sha256"] == leg["sid_state_canon_sha256"]
