import json, subprocess, sys
from pathlib import Path
from tempfile import TemporaryDirectory

def run_verify(sol, cont):
    cmd = [sys.executable,"-m","cli.verify",str(sol),str(cont)]
    return subprocess.run(cmd, capture_output=True, text=True)

def test_verify_valid_solution(tmp_path):
    # minimal 4-cell container solvable by piece A=1
    cont = {"lattice_type":"fcc","coordinates":[[0,0,0],[1,0,0],[0,1,0],[1,1,0]]}
    cpath = tmp_path/"c.json"; cpath.write_text(json.dumps(cont))
    sol = {
      "placements":[{"piece":"A","ori":8,"t":[1,1,0]}],  # Valid placement that covers all 4 cells
      "sid_state_canon_sha256": "dummy"
    }
    # recompute correct sid
    from src.io.solution_sig import canonical_state_signature
    from src.solver.symbreak import container_symmetry_group
    cells_sorted = [(0,0,0),(1,0,0),(0,1,0),(1,1,0)]
    symGroup = container_symmetry_group(cells_sorted)
    covered = {(0,0,0),(1,0,0),(0,1,0),(1,1,0)}
    sol["sid_state_canon_sha256"] = canonical_state_signature(covered, symGroup)
    spath = tmp_path/"s.json"; spath.write_text(json.dumps(sol))
    r = run_verify(spath,cpath)
    assert r.returncode == 0
    assert "solution verified ok" in r.stdout.lower()

def test_verify_fails_on_overlap(tmp_path):
    cont = {"lattice_type":"fcc","coordinates":[[0,0,0],[1,0,0]]}
    cpath = tmp_path/"c.json"; cpath.write_text(json.dumps(cont))
    # This placement covers 4 cells but container only has 2 - will cause overlap/out-of-bounds
    sol = {"placements":[{"piece":"A","ori":0,"t":[0,0,0]}],"sid_state_canon_sha256":"bad"}
    spath = tmp_path/"s.json"; spath.write_text(json.dumps(sol))
    r = run_verify(spath,cpath)
    assert r.returncode == 2
    assert "solution verified ok" not in r.stdout.lower()

def test_verify_fails_on_missing_cells(tmp_path):
    cont = {"lattice_type":"fcc","coordinates":[[0,0,0],[1,0,0],[0,1,0],[1,1,0],[2,0,0]]}
    cpath = tmp_path/"c.json"; cpath.write_text(json.dumps(cont))
    # Only covers 4 cells but container has 5
    sol = {"placements":[{"piece":"A","ori":8,"t":[1,1,0]}],"sid_state_canon_sha256":"bad"}
    spath = tmp_path/"s.json"; spath.write_text(json.dumps(sol))
    r = run_verify(spath,cpath)
    assert r.returncode == 2
    assert "missing cells" in r.stdout.lower()

def test_verify_fails_on_sid_mismatch(tmp_path):
    cont = {"lattice_type":"fcc","coordinates":[[0,0,0],[1,0,0],[0,1,0],[1,1,0]]}
    cpath = tmp_path/"c.json"; cpath.write_text(json.dumps(cont))
    sol = {
      "placements":[{"piece":"A","ori":8,"t":[1,1,0]}],
      "sid_state_canon_sha256": "wrong_signature"
    }
    spath = tmp_path/"s.json"; spath.write_text(json.dumps(sol))
    r = run_verify(spath,cpath)
    assert r.returncode == 2
    assert "canonical sid mismatch" in r.stdout.lower()
