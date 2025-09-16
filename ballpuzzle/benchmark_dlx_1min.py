#!/usr/bin/env python3
"""Benchmark DLX engine for 1 minute and count solutions found."""

import json
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.solver.registry import get_engine
from src.io.container import load_container

def main():
    # Load container and inventory
    container = load_container("data/containers/legacy_fixed/16 cell container.json")
    
    with open("test_inventory_all_pieces.json", "r") as f:
        inventory_data = json.load(f)
    
    # Setup options with 60-second time limit
    options = {
        "seed": 42,
        "max_results": 10000,  # High limit to not stop early
        "time_limit_seconds": 60,  # 1 minute limit
        "flags": {"mrvPieces": False, "supportBias": False},
        "caps": {"maxNodes": 0, "maxDepth": 0, "maxRows": 0},
        "progress_interval_ms": 0
    }
    
    # Get DLX engine
    engine = get_engine("dlx")
    pieces = {}  # Not used by DLX
    
    print("Starting DLX benchmark for 60 seconds...")
    start_time = time.time()
    
    solution_count = 0
    last_report_time = start_time
    
    try:
        for event in engine.solve(container, inventory_data, pieces, options):
            if event.get("type") == "solution":
                solution_count += 1
                current_time = time.time()
                
                # Report progress every 10 seconds
                if current_time - last_report_time >= 10:
                    elapsed = current_time - start_time
                    rate = solution_count / elapsed if elapsed > 0 else 0
                    print(f"Progress: {elapsed:.1f}s elapsed, {solution_count} solutions found ({rate:.2f} solutions/sec)")
                    last_report_time = current_time
            
            elif event.get("type") == "done":
                break
    
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"\n=== DLX Benchmark Results ===")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"Solutions found: {solution_count}")
    print(f"Solutions per second: {solution_count / elapsed_time:.2f}")
    print(f"Average time per solution: {elapsed_time / solution_count:.3f} seconds" if solution_count > 0 else "No solutions found")

if __name__ == "__main__":
    main()
