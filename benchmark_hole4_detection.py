#!/usr/bin/env python3
"""
Benchmark DFS engine with and without hole4 detection for 30 seconds each.
Compare solution counts to measure pruning effectiveness.
"""

import subprocess
import json
import time
import os
from pathlib import Path

def run_dfs_benchmark(use_hole4: bool, duration: int = 30) -> dict:
    """Run DFS engine benchmark with or without hole4 detection."""
    
    # Build command
    cmd = [
        "python", "-m", "cli.solve",
        "data/containers/legacy_fixed/16 cell container.json",
        "--engine", "dfs",
        "--time-limit", str(duration),
        "--max-results", "1000",  # High limit to not constrain by solution count
        "--pieces", "A=1,B=1,C=1,D=1,E=1,F=1,G=1,H=1,I=1,J=1,K=1,L=1,M=1,N=1,O=1,P=1,Q=1,R=1,S=1,T=1,U=1,V=1,W=1,X=1,Y=1"
    ]
    
    if use_hole4:
        cmd.append("--hole4")
    
    print(f"Running DFS benchmark {'WITH' if use_hole4 else 'WITHOUT'} hole4 detection for {duration} seconds...")
    print(f"Command: {' '.join(cmd)}")
    
    # Run benchmark
    start_time = time.time()
    result = subprocess.run(cmd, cwd="C:\\Ball Puzzle\\ballpuzzle", 
                          capture_output=True, text=True)
    end_time = time.time()
    
    actual_duration = end_time - start_time
    
    # Parse results
    solution_count = 0
    try:
        # Try to read solution.json if it exists
        solution_file = Path("C:\\Ball Puzzle\\ballpuzzle\\solution.json")
        if solution_file.exists():
            with open(solution_file, 'r') as f:
                solution_data = json.load(f)
                if 'solutions' in solution_data:
                    solution_count = len(solution_data['solutions'])
                elif 'placements' in solution_data:
                    solution_count = 1  # Single solution format
        
        # Also try to count from events.jsonl
        events_file = Path("C:\\Ball Puzzle\\ballpuzzle\\events.jsonl")
        if events_file.exists():
            event_solution_count = 0
            with open(events_file, 'r') as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if event.get('type') == 'solution':
                            event_solution_count += 1
            # Use the higher count (events are more reliable)
            if event_solution_count > solution_count:
                solution_count = event_solution_count
                
    except Exception as e:
        print(f"Error parsing results: {e}")
    
    return {
        'hole4_enabled': use_hole4,
        'duration_requested': duration,
        'duration_actual': actual_duration,
        'solution_count': solution_count,
        'exit_code': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr
    }

def main():
    """Run benchmark comparison."""
    print("=" * 60)
    print("DFS Engine Hole4 Detection Benchmark")
    print("=" * 60)
    
    # Test without hole4 detection first
    results_without = run_dfs_benchmark(use_hole4=False, duration=30)
    
    print("\n" + "=" * 60)
    print("Waiting 2 seconds between tests...")
    time.sleep(2)
    
    # Test with hole4 detection
    results_with = run_dfs_benchmark(use_hole4=True, duration=30)
    
    # Display results
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    
    print(f"\nWITHOUT hole4 detection:")
    print(f"  Duration: {results_without['duration_actual']:.2f} seconds")
    print(f"  Solutions found: {results_without['solution_count']}")
    print(f"  Solutions per second: {results_without['solution_count'] / results_without['duration_actual']:.2f}")
    print(f"  Exit code: {results_without['exit_code']}")
    
    print(f"\nWITH hole4 detection:")
    print(f"  Duration: {results_with['duration_actual']:.2f} seconds")
    print(f"  Solutions found: {results_with['solution_count']}")
    print(f"  Solutions per second: {results_with['solution_count'] / results_with['duration_actual']:.2f}")
    print(f"  Exit code: {results_with['exit_code']}")
    
    # Calculate improvement
    if results_without['solution_count'] > 0 and results_with['solution_count'] > 0:
        throughput_without = results_without['solution_count'] / results_without['duration_actual']
        throughput_with = results_with['solution_count'] / results_with['duration_actual']
        
        if throughput_without > 0:
            improvement = ((throughput_with - throughput_without) / throughput_without) * 100
            print(f"\nPERFORMANCE COMPARISON:")
            print(f"  Throughput improvement: {improvement:+.1f}%")
            
            if improvement > 0:
                print(f"  [+] Hole4 detection IMPROVED performance by {improvement:.1f}%")
            elif improvement < -5:
                print(f"  [-] Hole4 detection REDUCED performance by {abs(improvement):.1f}%")
            else:
                print(f"  [=] Hole4 detection had minimal impact ({improvement:+.1f}%)")
    
    # Show any errors
    if results_without['stderr']:
        print(f"\nErrors WITHOUT hole4:")
        print(results_without['stderr'])
    
    if results_with['stderr']:
        print(f"\nErrors WITH hole4:")
        print(results_with['stderr'])
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
