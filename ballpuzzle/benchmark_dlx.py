#!/usr/bin/env python3

import json
import time
from src.solver.engines.dlx_engine import DLXEngine

def benchmark_dlx(time_limit_seconds=10):
    """Benchmark DLX engine and count solutions found."""
    
    # Load 16-cell container
    with open("data/containers/legacy_fixed/16 cell container.json", 'r') as f:
        container = json.load(f)
    
    # All 25 pieces, 1 each
    inventory = {chr(65 + i): 1 for i in range(25)}  # A=1, B=1, ..., Y=1
    pieces = list(inventory.keys())
    
    print(f"Starting DLX benchmark for {time_limit_seconds} seconds...")
    print(f"Container: 16-cell container ({len(container['coordinates'])} coordinates)")
    print(f"Inventory: {inventory}")
    print(f"Total pieces: {len(pieces)}")
    print()
    
    # Initialize engine
    engine = DLXEngine()
    options = {
        'time_limit': time_limit_seconds,
        'seed': 42,
        'max_results': float('inf')  # Allow unlimited solutions
    }
    
    # Track solutions and combinations
    solutions_found = 0
    combinations_tested = 0
    candidates_generated = 0
    start_time = time.time()
    last_debug_time = start_time
    
    # Run engine
    try:
        for event in engine.solve(container, inventory, pieces, options):
            if event['type'] == 'solution':
                solutions_found += 1
                elapsed = time.time() - start_time
                print(f"Solution {solutions_found} found at {elapsed:.1f}s")
                
            elif event['type'] == 'tick':
                # Track progress
                elapsed = time.time() - start_time
                if elapsed - (last_debug_time - start_time) >= 2.0:  # Every 2 seconds
                    print(f"Progress: {elapsed:.1f}s elapsed, {solutions_found} solutions found")
                    last_debug_time = time.time()
                
            elif event['type'] == 'done':
                break
                
    except Exception as e:
        print(f"Engine stopped: {e}")
    
    elapsed_time = time.time() - start_time
    
    print()
    print("=== BENCHMARK RESULTS ===")
    print(f"Time limit: {time_limit_seconds} seconds")
    print(f"Actual runtime: {elapsed_time:.2f} seconds")
    print(f"Solutions found: {solutions_found}")
    if elapsed_time > 0:
        print(f"Solutions per second: {solutions_found / elapsed_time:.2f}")
    print()
    
    return solutions_found, elapsed_time

if __name__ == "__main__":
    # Test 10 seconds first
    print("=== 10-Second Benchmark ===")
    solutions_10s, time_10s = benchmark_dlx(10)
    
    print("\n" + "="*50 + "\n")
    
    # Test 30 seconds
    print("=== 30-Second Benchmark ===")
    solutions_30s, time_30s = benchmark_dlx(30)
    
    print("\n=== SUMMARY ===")
    print(f"10s test: {solutions_10s} solutions in {time_10s:.1f}s")
    print(f"30s test: {solutions_30s} solutions in {time_30s:.1f}s")
