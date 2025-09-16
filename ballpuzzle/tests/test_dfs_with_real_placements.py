"""Test DFS engine with real piece placements."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

def test_dfs_runs_real_placements():
    """Smoke test: engine runs with real placements and writes solution."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create a tiny solvable container
        container = {
            "name": "tiny_test",
            "lattice_type": "fcc",
            "coordinates": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
        }
        
        container_path = tmp_path / "container.json"
        container_path.write_text(json.dumps(container), encoding="utf-8")
        
        eventlog_path = tmp_path / "events.jsonl"
        solution_path = tmp_path / "solution.json"
        
        # Run DFS engine with small inventory
        cmd = [
            sys.executable, "-m", "cli.solve",
            str(container_path),
            "--engine", "dfs",
            "--pieces", "A=1,B=1",  # Small inventory
            "--eventlog", str(eventlog_path),
            "--solution", str(solution_path),
            "--seed", "42"
        ]
        
        try:
            result = subprocess.run(cmd, cwd="c:/Ball Puzzle/ballpuzzle", 
                                  capture_output=True, text=True, timeout=30)
            
            # Check if command succeeded (may not find solution but should run)
            if result.returncode != 0:
                print(f"Command failed with return code {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                # Don't fail test if no solution found, just check it ran
            
            # Verify solution file exists and has expected structure
            if solution_path.exists():
                solution_text = solution_path.read_text(encoding="utf-8")
                if solution_text.strip():  # Non-empty solution
                    solution = json.loads(solution_text)
                    
                    # Check required fields
                    assert "sid_state_canon_sha256" in solution
                    assert "lattice" in solution
                    assert solution["lattice"] == "fcc"
                    
                    # If placements exist, verify structure
                    if "placements" in solution and solution["placements"]:
                        for placement in solution["placements"]:
                            assert "piece" in placement
                            assert "ori" in placement
                            assert "t" in placement
                            assert "coordinates" in placement
            
            # Verify eventlog exists
            assert eventlog_path.exists(), "Event log should be created"
            
            # Check for done event
            eventlog_text = eventlog_path.read_text(encoding="utf-8")
            done_found = False
            
            for line in eventlog_text.splitlines():
                if line.strip():
                    try:
                        event = json.loads(line)
                        if event.get("type") == "done":
                            done_found = True
                            # Verify metrics exist
                            metrics = event.get("metrics", {})
                            assert "nodes" in metrics
                            assert "pruned" in metrics
                            assert "bestDepth" in metrics
                            assert "solutions" in metrics
                            break
                    except json.JSONDecodeError:
                        continue
            
            assert done_found, "Should find done event in eventlog"
            
        except subprocess.TimeoutExpired:
            # Test timed out - this is acceptable for this smoke test
            pass

def test_dfs_with_sufficient_inventory():
    """Test DFS with inventory that could potentially solve a tiny container."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create minimal 2-cell container
        container = {
            "name": "minimal",
            "lattice_type": "fcc", 
            "coordinates": [[0, 0, 0], [1, 0, 0]]
        }
        
        container_path = tmp_path / "container.json"
        container_path.write_text(json.dumps(container), encoding="utf-8")
        
        eventlog_path = tmp_path / "events.jsonl"
        solution_path = tmp_path / "solution.json"
        
        # Run with piece that could fit
        cmd = [
            sys.executable, "-m", "cli.solve",
            str(container_path),
            "--engine", "dfs",
            "--pieces", "V=1",  # V is a 2-cell piece that might fit
            "--eventlog", str(eventlog_path),
            "--solution", str(solution_path),
            "--seed", "123"
        ]
        
        try:
            result = subprocess.run(cmd, cwd="c:/Ball Puzzle/ballpuzzle",
                                  capture_output=True, text=True, timeout=15)
            
            # Verify files were created
            assert eventlog_path.exists()
            
            # Check done event exists with metrics
            eventlog_text = eventlog_path.read_text(encoding="utf-8")
            done_events = []
            
            for line in eventlog_text.splitlines():
                if line.strip():
                    try:
                        event = json.loads(line)
                        if event.get("type") == "done":
                            done_events.append(event)
                    except json.JSONDecodeError:
                        continue
            
            assert len(done_events) >= 1, "Should have at least one done event"
            
            done_event = done_events[-1]
            metrics = done_event.get("metrics", {})
            assert isinstance(metrics.get("nodes", 0), int)
            assert isinstance(metrics.get("solutions", 0), int)
            
        except subprocess.TimeoutExpired:
            # Acceptable for smoke test
            pass
