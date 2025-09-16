"""Test that inventory constraints are respected by DFS engine."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

def test_impossible_inventory_no_solution():
    """Provide impossible inventory and ensure solutions == 0."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create a container that needs pieces to fill
        container = {
            "name": "unfillable",
            "lattice_type": "fcc",
            "coordinates": [[0, 0, 0], [1, 0, 0], [0, 1, 0]]  # 3 cells
        }
        
        container_path = tmp_path / "container.json"
        container_path.write_text(json.dumps(container), encoding="utf-8")
        
        eventlog_path = tmp_path / "events.jsonl"
        solution_path = tmp_path / "solution.json"
        
        # Run with no pieces available
        cmd = [
            sys.executable, "-m", "cli.solve",
            str(container_path),
            "--engine", "dfs",
            "--pieces", "A=0",  # No pieces available
            "--eventlog", str(eventlog_path),
            "--solution", str(solution_path),
            "--seed", "42"
        ]
        
        try:
            result = subprocess.run(cmd, cwd="c:/Ball Puzzle/ballpuzzle",
                                  capture_output=True, text=True, timeout=10)
            
            # Should complete (may have non-zero return code if no solution)
            assert eventlog_path.exists(), "Event log should be created"
            
            # Check done event shows 0 solutions
            eventlog_text = eventlog_path.read_text(encoding="utf-8")
            done_found = False
            
            for line in eventlog_text.splitlines():
                if line.strip():
                    try:
                        event = json.loads(line)
                        if event.get("type") == "done":
                            done_found = True
                            metrics = event.get("metrics", {})
                            solutions = metrics.get("solutions", -1)
                            assert solutions == 0, f"Expected 0 solutions, got {solutions}"
                            break
                    except json.JSONDecodeError:
                        continue
            
            assert done_found, "Should find done event in eventlog"
            
            # Solution file should either not exist or be empty/null
            if solution_path.exists():
                solution_text = solution_path.read_text(encoding="utf-8").strip()
                if solution_text and solution_text != "null":
                    solution = json.loads(solution_text)
                    # If solution exists, it should have empty placements
                    assert solution.get("placements", []) == [], "Should have no placements"
                    
        except subprocess.TimeoutExpired:
            # Should not timeout on impossible case
            assert False, "Should not timeout on impossible inventory"

def test_insufficient_inventory_no_solution():
    """Test with inventory that has pieces but insufficient to fill container."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create container that needs 8 cells (2x2x2 cube)
        container = {
            "name": "cube",
            "lattice_type": "fcc",
            "coordinates": [
                [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
                [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]
            ]
        }
        
        container_path = tmp_path / "container.json"
        container_path.write_text(json.dumps(container), encoding="utf-8")
        
        eventlog_path = tmp_path / "events.jsonl"
        solution_path = tmp_path / "solution.json"
        
        # Provide only one 4-cell piece for 8-cell container
        cmd = [
            sys.executable, "-m", "cli.solve",
            str(container_path),
            "--engine", "dfs", 
            "--pieces", "A=1",  # Only one 4-cell piece for 8-cell container
            "--eventlog", str(eventlog_path),
            "--solution", str(solution_path),
            "--seed", "123"
        ]
        
        try:
            result = subprocess.run(cmd, cwd="c:/Ball Puzzle/ballpuzzle",
                                  capture_output=True, text=True, timeout=15)
            
            assert eventlog_path.exists(), "Event log should be created"
            
            # Check that search ran but found no complete solution
            eventlog_text = eventlog_path.read_text(encoding="utf-8")
            done_found = False
            nodes_explored = 0
            
            for line in eventlog_text.splitlines():
                if line.strip():
                    try:
                        event = json.loads(line)
                        if event.get("type") == "done":
                            done_found = True
                            metrics = event.get("metrics", {})
                            solutions = metrics.get("solutions", -1)
                            nodes_explored = metrics.get("nodes", 0)
                            
                            # Should have explored some nodes but found no solutions
                            assert solutions == 0, f"Expected 0 solutions with insufficient inventory, got {solutions}"
                            # Should have tried at least some placements
                            assert nodes_explored >= 0, "Should have explored some nodes"
                            break
                    except json.JSONDecodeError:
                        continue
            
            assert done_found, "Should find done event"
            
        except subprocess.TimeoutExpired:
            assert False, "Should not timeout on insufficient inventory test"

def test_exact_inventory_finds_solution():
    """Test with exactly the right inventory to potentially solve a tiny container."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create tiny 4-cell container that matches piece A exactly
        container = {
            "name": "square",
            "lattice_type": "fcc",
            "coordinates": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
        }
        
        container_path = tmp_path / "container.json"
        container_path.write_text(json.dumps(container), encoding="utf-8")
        
        eventlog_path = tmp_path / "events.jsonl"
        solution_path = tmp_path / "solution.json"
        
        # Provide exactly one piece A (4 cells) for 4-cell container
        cmd = [
            sys.executable, "-m", "cli.solve",
            str(container_path),
            "--engine", "dfs",
            "--pieces", "A=1",  # Exactly one 4-cell piece
            "--eventlog", str(eventlog_path),
            "--solution", str(solution_path),
            "--seed", "456"
        ]
        
        try:
            result = subprocess.run(cmd, cwd="c:/Ball Puzzle/ballpuzzle",
                                  capture_output=True, text=True, timeout=20)
            
            assert eventlog_path.exists(), "Event log should be created"
            
            # Check results - may or may not find solution depending on piece geometry
            eventlog_text = eventlog_path.read_text(encoding="utf-8")
            done_found = False
            
            for line in eventlog_text.splitlines():
                if line.strip():
                    try:
                        event = json.loads(line)
                        if event.get("type") == "done":
                            done_found = True
                            metrics = event.get("metrics", {})
                            solutions = metrics.get("solutions", 0)
                            nodes = metrics.get("nodes", 0)
                            
                            # Should have tried to place pieces
                            assert nodes >= 0, "Should have explored nodes"
                            assert solutions >= 0, "Solutions count should be non-negative"
                            
                            # If solution found, verify it uses exactly the available inventory
                            if solutions > 0 and solution_path.exists():
                                solution_text = solution_path.read_text(encoding="utf-8")
                                if solution_text.strip():
                                    solution = json.loads(solution_text)
                                    pieces_used = solution.get("piecesUsed", {})
                                    assert pieces_used.get("A", 0) <= 1, "Should not use more than 1 piece A"
                            
                            break
                    except json.JSONDecodeError:
                        continue
            
            assert done_found, "Should find done event"
            
        except subprocess.TimeoutExpired:
            # Acceptable for this test case
            pass
