#!/usr/bin/env python3
"""
Benchmark DLX engine with unique pieces inventory (1 of each A-Y) for 1 minute.
"""

import sys
import os
import time
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from solver.engines.registry import get_engine
from io.container import load_container

def main():
    # Load 16-cell container
    container_path = "data/containers/Shape_10.container.json"
    container = load_container(container_path)
    container_size = len(container["coordinates"])
    
    print(f"Benchmarking DLX engine with unique pieces inventory")
    print(f"Container: {container_path} ({container_size} cells)")
    print(f"Inventory: 1 of each piece A-Y (unique pieces only)")
    print(f"Expected combinations: 12,650")
    print(f"Time limit: 60 seconds")
    print()
    
    # Create unique pieces inventory (1 of each A-Y)
    unique_inventory = {chr(65 + i): 1 for i in range(25)}  # A-Y, 1 each
    
    # Get DLX engine
    engine_class = get_engine("dlx")
    engine = engine_class()
    
    # Configure engine options
    options = {
        "max_results": 10000,  # High limit to not constrain by count
        "time_limit_seconds": 60,  # 1 minute time limit
        "seed": 42  # Fixed seed for reproducibility
    }
    
    print("Starting DLX benchmark...")
    start_time = time.time()
    
    solution_count = 0
    combination_count = 0
    
    # Run solver and count solutions
    for event in engine.solve(container, unique_inventory, **options):
        if event.get("type") == "solution":
            solution_count += 1
            if solution_count == 1:
                print(f"First solution found at {time.time() - start_time:.1f}s")
        elif event.get("type") == "tick":
            # Track combination progress
            if "combinationsTested" in event:
                combination_count = event["combinationsTested"]
        elif event.get("type") == "done":
            break
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    print()
    print("=== BENCHMARK RESULTS ===")
    print(f"Total runtime: {elapsed:.1f} seconds")
    print(f"Solutions found: {solution_count:,}")
    print(f"Combinations tested: {combination_count:,}")
    print(f"Solution rate: {solution_count / elapsed:.2f} solutions/second")
    print(f"Combination rate: {combination_count / elapsed:.1f} combinations/second")
    
    if solution_count > 0:
        print(f"Average time per solution: {elapsed / solution_count:.3f} seconds")
    
    print()
    print("Comparison with previous benchmark (2 of each piece):")
    print("- Previous: 230 solutions in 60s (3.83 solutions/second)")
    print(f"- Current:  {solution_count} solutions in {elapsed:.0f}s ({solution_count / elapsed:.2f} solutions/second)")

if __name__ == "__main__":
    main()
