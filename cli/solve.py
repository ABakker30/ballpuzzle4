import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.solver.registry import get_engine
from src.io.container import load_container
from src.io.solution import write_solution
from src.io.snapshot import open_eventlog, write_event
from src.reporting.exporters import tty_info, tty_progress

def main():
    parser = argparse.ArgumentParser(description="Ball Puzzle Solver")
    parser.add_argument("container", help="Container JSON file")
    parser.add_argument("--engine", default="current", help="Engine name")
    parser.add_argument("--eventlog", help="Event log output file")
    parser.add_argument("--solution", help="Solution output file")
    args = parser.parse_args()

    # Load container
    tty_info(f"Loading container from {args.container}")
    container_data = load_container(args.container)
    
    # Get engine
    engine = get_engine(args.engine)
    tty_info(f"Using engine: {engine.name}")
    
    # Open event log if specified
    eventlog_fp = None
    if args.eventlog:
        eventlog_fp = open_eventlog(args.eventlog)
        tty_info(f"Event log: {args.eventlog}")
    
    # Run solver
    tty_progress("Starting solver")
    
    # Minimal stub data
    inventory = {}
    pieces = {}
    options = {}
    
    for event in engine.solve(container_data, inventory, pieces, options):
        if eventlog_fp:
            write_event(event, eventlog_fp)
        
        if event["type"] == "tick":
            tty_progress(f"Progress: {event['metrics']}")
        elif event["type"] == "done":
            tty_info(f"Solver finished: {event['metrics']}")
    
    if eventlog_fp:
        eventlog_fp.close()
    
    # Write solution if specified
    if args.solution:
        solution_data = {
            "lattice": "fcc",
            "containerCidSha256": container_data.get("cid_sha256", "stub"),
            "placements": [],
            "piecesUsed": {},
            "sid_state_sha256": "stub_state",
            "sid_route_sha256": "stub_route"
        }
        meta = {
            "engine": args.engine,
            "seed": None,
            "flags": {}
        }
        write_solution(args.solution, solution_data, meta)
        tty_info(f"Solution written to {args.solution}")

if __name__ == "__main__":
    main()
