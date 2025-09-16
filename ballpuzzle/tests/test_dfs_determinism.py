import json, subprocess, sys, tempfile, shutil, os

def run_once(seed):
    d = tempfile.mkdtemp()
    try:
        cpath = os.path.join(d, "c.json")
        with open(cpath,"w",encoding="utf-8") as f:
            f.write(json.dumps({"name": "tiny", "lattice_type": "fcc", "coordinates": [[0,0,0],[1,0,0],[0,1,0]]}))
        ev = os.path.join(d,"events.jsonl")
        sol = os.path.join(d,"solution.json")
        subprocess.check_call([sys.executable,"-m","cli.solve",cpath,"--engine","dfs","--eventlog",ev,"--solution",sol,"--seed",str(seed)])
        return open(ev,"r",encoding="utf-8").read()
    finally:
        shutil.rmtree(d)

def test_dfs_deterministic_by_seed():
    a = run_once(111)
    b = run_once(111)
    c = run_once(222)
    
    # Parse and normalize events (ignore timing)
    def normalize_events(event_text):
        events = []
        for line in event_text.strip().split('\n'):
            if line:
                event = json.loads(line)
                # Remove timing field for comparison
                if 't_ms' in event:
                    del event['t_ms']
                events.append(event)
        return events
    
    a_events = normalize_events(a)
    b_events = normalize_events(b)
    c_events = normalize_events(c)
    
    assert a_events == b_events  # Same seed should give same behavior
    assert a_events != c_events  # Different seeds should differ
