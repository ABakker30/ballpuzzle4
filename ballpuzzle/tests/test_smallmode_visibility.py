import json, subprocess, sys, re
from pathlib import Path

def test_smallmode_fields_in_events(tmp_path):
    # tiny container: 2 cells => smallMode True
    cont = {"name": "tiny", "lattice_type": "fcc", "coordinates": [[0,0,0],[1,0,0]]}
    cpath = tmp_path/"c.json"; cpath.write_text(json.dumps(cont), encoding="utf-8")
    ev = tmp_path/"events.jsonl"; sol = tmp_path/"solution.json"

    cmd = [sys.executable, "-m", "cli.solve", str(cpath), "--engine", "current",
           "--eventlog", str(ev), "--solution", str(sol), "--seed", "123"]
    subprocess.check_call(cmd)

    # Scan events for a tick with the fields
    found = False
    for line in ev.read_text(encoding="utf-8").splitlines():
        data = json.loads(line)
        if data.get("type") == "tick":
            m = data.get("metrics", {})
            if {"smallMode","symGroup","seed","ttEnabled"}.issubset(m.keys()):
                assert m["smallMode"] is True
                assert isinstance(m["symGroup"], int) and m["symGroup"] >= 1
                assert m["seed"] == 123
                assert m["ttEnabled"] is True
                assert isinstance(m.get("probe"), list)
                found = True
                break
    assert found, "expected small-mode fields in tick events"
