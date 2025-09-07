import json, subprocess, sys
from pathlib import Path
from tempfile import TemporaryDirectory

def run_both(cells, pieces="A=1", seed=123):
    with TemporaryDirectory() as d:
        d = Path(d)
        c = d/"c.json"; c.write_text(json.dumps({"name":"test_container","lattice_type":"fcc","coordinates":cells}), encoding="utf-8")
        def run(engine):
            ev = d/f"e_{engine}.jsonl"; sol = d/f"s_{engine}.json"
            cmd = [sys.executable,"-m","cli.solve",str(c),
                   "--engine",engine,"--pieces",pieces,
                   "--eventlog",str(ev),"--solution",str(sol),"--seed","123","--max-results","1"]
            subprocess.check_call(cmd)
            return json.loads(sol.read_text(encoding="utf-8"))
        dfs = run("dfs")
        dlx = run("dlx")
        return dfs, dlx

def test_canonical_sid_parity_tiny_4():
    cells = [[0,0,0],[1,0,0],[0,1,0],[1,1,0]]
    dfs, dlx = run_both(cells, pieces="A=1")
    assert dfs["sid_state_canon_sha256"] == dlx["sid_state_canon_sha256"]
