import subprocess
import tempfile
import json
from pathlib import Path
import sys

def test_cli_runs():
    """Test that CLI runs without error and produces expected files."""
    
    # Create a minimal container file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        container_data = {
            "name": "test_container",
            "lattice_type": "fcc", 
            "coordinates": [[0,0,0], [1,0,0]]
        }
        json.dump(container_data, f)
        container_file = f.name
    
    try:
        # Test basic CLI run
        with tempfile.TemporaryDirectory() as tmpdir:
            eventlog_file = Path(tmpdir) / "events.jsonl"
            solution_file = Path(tmpdir) / "solution.json"
            
            # Run CLI
            result = subprocess.run([
                sys.executable, "-m", "cli.solve",
                container_file,
                "--engine", "current",
                "--eventlog", str(eventlog_file),
                "--solution", str(solution_file)
            ], cwd=Path(__file__).parent.parent, capture_output=True, text=True)
            
            # Check CLI ran successfully
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            
            # Check event log was created
            assert eventlog_file.exists(), "Event log file not created"
            
            # Check solution file was created
            assert solution_file.exists(), "Solution file not created"
            
            # Verify event log format
            with open(eventlog_file) as f:
                lines = f.readlines()
                assert len(lines) > 0, "Event log is empty"
                
                for line in lines:
                    event = json.loads(line.strip())
                    assert "v" in event, "Event missing version"
                    assert event["v"] == 1, "Event version incorrect"
            
            # Verify solution format
            with open(solution_file) as f:
                solution = json.load(f)
                assert solution["version"] == 1, "Solution version incorrect"
                assert solution["lattice"] == "fcc", "Solution lattice incorrect"
                assert "solver" in solution, "Solution missing solver info"
                assert solution["solver"]["engine"] == "current", "Solution engine incorrect"
    
    finally:
        # Clean up
        Path(container_file).unlink()

if __name__ == "__main__":
    test_cli_runs()
    print("CLI wire test passed!")
