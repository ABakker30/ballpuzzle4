import json, subprocess, sys
from pathlib import Path

def _tiny_container(tmp_path: Path):
    cont = {"name": "tiny", "lattice_type": "fcc", "coordinates": [[0,0,0],[1,0,0],[0,1,0]]}
    cpath = tmp_path/"c.json"
    cpath.write_text(json.dumps(cont), encoding="utf-8")
    return cpath

def test_dfs_engine_emits_solution_and_done(tmp_path):
    cpath = _tiny_container(tmp_path)
    ev = tmp_path/"events.jsonl"
    sol = tmp_path/"solution.json"
    cmd = [sys.executable, "-m", "cli.solve", str(cpath),
           "--engine","dfs","--eventlog",str(ev),"--solution",str(sol),"--seed","123"]
    subprocess.check_call(cmd)
    data = json.loads(sol.read_text(encoding="utf-8"))
    assert data["lattice"] == "fcc" and "containerCidSha256" in data
    # eventlog should contain 'done' with nodes/pruned/bestDepth/smallMode/symGroup/seed
    found_done = False
    for line in ev.read_text(encoding="utf-8").splitlines():
        evt = json.loads(line)
        if evt.get("type") == "done":
            m = evt.get("metrics", {})
            for k in ("nodes","pruned","bestDepth","smallMode","symGroup","seed"):
                assert k in m
            found_done = True
            break
    assert found_done
