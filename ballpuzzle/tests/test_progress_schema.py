import json, subprocess, sys, time
from pathlib import Path
from tempfile import TemporaryDirectory

def test_tick_emission_and_schema_validation():
    with TemporaryDirectory() as d:
        d = Path(d)
        ev = d/"e.jsonl"; sol = d/"s.json"
        # Use existing container that will generate search activity
        container_path = Path(__file__).parent / "data" / "containers" / "tiny_20.fcc.json"
        cmd = [sys.executable,"-m","cli.solve",str(container_path),
               "--engine","dfs","--pieces","A=1,B=1,C=1",
               "--eventlog",str(ev),"--solution",str(sol),
               "--seed","123","--progress-interval-ms","1",
               "--caps-max-nodes","1000"]
        subprocess.check_call(cmd)
        lines = ev.read_text(encoding="utf-8").splitlines()
        ticks = [json.loads(x) for x in lines if json.loads(x).get("type") == "tick"]
        assert len(ticks) >= 1, "expected at least one tick event"
        # minimal fields
        m = ticks[0]["metrics"]
        for k in ("nodes","pruned","depth","bestDepth","solutions"):
            assert k in m
