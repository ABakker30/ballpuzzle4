import json, subprocess, sys
from pathlib import Path
from tempfile import TemporaryDirectory

def test_legacy_engine_runs_cli_tiny4():
    with TemporaryDirectory() as d:
        d = Path(d)
        c = d/"c.json"; ev = d/"e.jsonl"; s = d/"s.json"
        c.write_text(json.dumps({"name":"tiny_4","lattice_type":"fcc","coordinates":[[0,0,0],[1,0,0],[0,1,0],[1,1,0]]}), encoding="utf-8")
        cmd = [sys.executable,"-m","cli.solve",str(c),
               "--engine","legacy","--pieces","A=1",
               "--eventlog",str(ev),"--solution",str(s),
               "--seed","123","--max-results","1"]
        subprocess.check_call(cmd)
        # solution file is written by CLI even if no solution from legacy
        # If bridge returns a solution, assert canonical field
        data = json.loads(s.read_text(encoding="utf-8"))
        assert "lattice" in data
