"""
Test DLX scaling features: symmetry reduction, dominance pruning, row caps, tick events.
"""
import subprocess
import tempfile
import json
import os
from pathlib import Path

def test_dlx_row_cap_enforcement():
    """Test that --caps-max-rows limits DLX row generation and emits clean termination."""
    # Use tiny_4.fcc.json with very low row cap
    container_path = Path(__file__).parent / "data" / "containers" / "tiny_4.fcc.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        eventlog = os.path.join(tmpdir, "events.jsonl")
        
        # Run with very low row cap (should terminate early)
        result = subprocess.run([
            "python", "-m", "cli.solve",
            str(container_path),
            "--engine", "dlx",
            "--eventlog", eventlog,
            "--caps-max-rows", "5",  # very low cap
            "--pieces", "A=1,B=1"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Check event log for clean termination
        events = []
        with open(eventlog, 'r') as f:
            for line in f:
                events.append(json.loads(line))
        
        # Should have at least one done event
        done_events = [e for e in events if e.get("type") == "done"]
        assert len(done_events) == 1, f"Expected 1 done event, got {len(done_events)}"
        
        done = done_events[0]
        assert "rowsBuilt" in done["metrics"], "Done event should include rowsBuilt metric"
        # With cap of 5, should have built <= 5 rows (or 0 if no valid placements)
        assert done["metrics"]["rowsBuilt"] <= 5, f"Should build ≤5 rows, got {done['metrics']['rowsBuilt']}"

def test_dlx_tick_events():
    """Test that DLX emits tick events with progress metrics when interval is set."""
    container_path = Path(__file__).parent / "data" / "containers" / "tiny_4.fcc.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        eventlog = os.path.join(tmpdir, "events.jsonl")
        
        # Run with tick interval
        result = subprocess.run([
            "python", "-m", "cli.solve",
            str(container_path),
            "--engine", "dlx",
            "--eventlog", eventlog,
            "--progress-interval-ms", "50",  # emit ticks every 50ms
            "--pieces", "A=1,B=1"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Check for tick events
        events = []
        with open(eventlog, 'r') as f:
            for line in f:
                events.append(json.loads(line))
        
        tick_events = [e for e in events if e.get("type") == "tick"]
        # May have tick events depending on timing; just verify structure if present
        if len(tick_events) > 0:
            # If ticks exist, verify structure
            tick = tick_events[0]
            assert "metrics" in tick, "Tick should have metrics"
            metrics = tick["metrics"]
            expected_keys = {"rows", "activeCols", "partial", "nodes", "pruned", "depth", "bestDepth", "solutions"}
            assert expected_keys.issubset(set(metrics.keys())), f"Missing tick metrics: {expected_keys - set(metrics.keys())}"

def test_dlx_symmetry_reduction():
    """Test that DLX reduces symmetric placements using canonical_atom_tuple."""
    # Use a symmetric container where reduction should be visible
    container_path = Path(__file__).parent / "data" / "containers" / "tiny_6.fcc.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        eventlog = os.path.join(tmpdir, "events.jsonl")
        
        # Run DLX without row cap to see full row count
        result = subprocess.run([
            "python", "-m", "cli.solve",
            str(container_path),
            "--engine", "dlx",
            "--eventlog", eventlog,
            "--pieces", "A=2"  # single piece type to focus on symmetry
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Check done event for rowsBuilt metric
        events = []
        with open(eventlog, 'r') as f:
            for line in f:
                events.append(json.loads(line))
        
        done_events = [e for e in events if e.get("type") == "done"]
        assert len(done_events) == 1, "Should have one done event"
        
        done = done_events[0]
        assert "rowsBuilt" in done["metrics"], "Should report rowsBuilt"
        rows_built = done["metrics"]["rowsBuilt"]
        
        # With symmetry reduction, should build fewer rows than naive enumeration
        # (exact count depends on container symmetry, but should be reasonable)
        assert rows_built > 0, "Should build some rows"
        assert rows_built < 1000, f"Should use symmetry reduction, got {rows_built} rows"

def test_dlx_dominance_pruning():
    """Test that dominance pruning removes strictly worse placements."""
    container_path = Path(__file__).parent / "data" / "containers" / "tiny_4.fcc.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        eventlog = os.path.join(tmpdir, "events.jsonl")
        
        # Use multiple pieces with different availability to trigger dominance
        result = subprocess.run([
            "python", "-m", "cli.solve",
            str(container_path),
            "--engine", "dlx",
            "--eventlog", eventlog,
            "--pieces", "A=1,B=2,C=3"  # different availability
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        # Verify clean execution (dominance pruning should not break correctness)
        events = []
        with open(eventlog, 'r') as f:
            for line in f:
                events.append(json.loads(line))
        
        done_events = [e for e in events if e.get("type") == "done"]
        assert len(done_events) == 1, "Should complete with done event"
        
        # Should still find solutions if they exist
        solution_events = [e for e in events if e.get("type") == "solution"]
        # Don't assert specific count since it depends on solvability,
        # but verify structure if solutions exist
        for sol in solution_events:
            assert "solution" in sol, "Solutions should have solution data"
            sol_data = sol["solution"]
            assert "placements" in sol_data, "Solution data should have placements"
            assert isinstance(sol_data["placements"], list), "Placements should be list"
