#!/usr/bin/env python3
"""
Benchmark script to compare DFS and DFS-Bitmask engines performance.
"""

import subprocess
import time
import json
import os
import sys
from pathlib import Path

def run_engine_benchmark(engine_name, container_path, time_limit, pieces_spec):
    """Run a single engine benchmark and return metrics."""
    
    # Create unique output files for this test
    events_file = f"events_{engine_name}_{int(time.time())}.jsonl"
    solution_file = f"solution_{engine_name}_{int(time.time())}.json"
    
    try:
        # Run the engine
        cmd = [
            sys.executable, "-m", "cli.solve",
            container_path,
            "--engine", engine_name,
            "--time-limit", str(time_limit),
            "--max-results", "1000",  # Allow many solutions
            "--eventlog", events_file,
            "--solution", solution_file
        ]
        
        if pieces_spec:
            cmd.extend(["--pieces", pieces_spec])
        
        print(f"Running {engine_name} engine for {time_limit} seconds...")
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        end_time = time.time()
        
        # Parse results
        solutions_found = 0
        nodes_explored = 0
        
        # Count solutions from events file
        if os.path.exists(events_file):
            with open(events_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("type") == "solution":
                            solutions_found += 1
                        elif event.get("type") == "done":
                            metrics = event.get("metrics", {})
                            nodes_explored = metrics.get("nodes_explored", 0)
                    except json.JSONDecodeError:
                        continue
        
        # Clean up temp files
        for temp_file in [events_file, solution_file]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return {
            "engine": engine_name,
            "solutions_found": solutions_found,
            "nodes_explored": nodes_explored,
            "runtime_seconds": end_time - start_time,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        return {
            "engine": engine_name,
            "error": str(e),
            "solutions_found": 0,
            "nodes_explored": 0,
            "runtime_seconds": 0,
            "exit_code": -1
        }

def main():
    # Test configuration
    container_path = "data/containers/legacy_fixed/16 cell container.json"
    time_limit = 30  # 30 seconds per engine
    pieces_spec = ""  # Use all pieces (default inventory)
    
    print("=== Bitmask DFS Engine Benchmark ===")
    print(f"Container: {container_path}")
    print(f"Time limit: {time_limit} seconds per engine")
    print(f"Pieces: {pieces_spec}")
    print()
    
    # Test engines
    engines = ["dfs", "dfs-bitmask"]
    results = {}
    
    for engine in engines:
        result = run_engine_benchmark(engine, container_path, time_limit, pieces_spec)
        results[engine] = result
        
        print(f"--- {engine.upper()} Engine Results ---")
        if result.get("error"):
            print(f"ERROR: {result['error']}")
        else:
            print(f"Solutions found: {result['solutions_found']}")
            print(f"Nodes explored: {result['nodes_explored']}")
            print(f"Runtime: {result['runtime_seconds']:.2f} seconds")
            print(f"Exit code: {result['exit_code']}")
            if result['solutions_found'] > 0:
                print(f"Solutions per second: {result['solutions_found'] / result['runtime_seconds']:.2f}")
        print()
    
    # Performance comparison
    if "dfs" in results and "dfs-bitmask" in results:
        dfs_result = results["dfs"]
        bitmask_result = results["dfs-bitmask"]
        
        print("=== Performance Comparison ===")
        
        if dfs_result['solutions_found'] > 0 and bitmask_result['solutions_found'] > 0:
            dfs_rate = dfs_result['solutions_found'] / dfs_result['runtime_seconds']
            bitmask_rate = bitmask_result['solutions_found'] / bitmask_result['runtime_seconds']
            
            print(f"DFS solutions/sec: {dfs_rate:.2f}")
            print(f"Bitmask DFS solutions/sec: {bitmask_rate:.2f}")
            
            if dfs_rate > 0:
                speedup = bitmask_rate / dfs_rate
                print(f"Bitmask speedup: {speedup:.2f}x")
        
        if dfs_result['nodes_explored'] > 0 and bitmask_result['nodes_explored'] > 0:
            node_ratio = bitmask_result['nodes_explored'] / dfs_result['nodes_explored']
            print(f"Bitmask nodes explored ratio: {node_ratio:.2f}x")
        
        print(f"DFS runtime: {dfs_result['runtime_seconds']:.2f}s")
        print(f"Bitmask runtime: {bitmask_result['runtime_seconds']:.2f}s")

if __name__ == "__main__":
    main()
