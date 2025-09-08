#!/usr/bin/env python3
"""
Analyze DLX solutions from a 1-minute benchmark test.
Captures solutions and reports piece usage patterns.
"""

import subprocess
import sys
import json
import time
from collections import defaultdict

def run_dlx_benchmark():
    """Run DLX engine for 60 seconds and capture all solutions."""
    print("Starting 1-minute DLX benchmark test...")
    print("Container: 16-cell container")
    print("Pieces: All 25 pieces (A-Y), 1 each")
    print("Time limit: 60 seconds")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "cli.solve",
        "data/containers/legacy_fixed/16 cell container.json",
        "--engine", "dlx",
        "--seed", "42",
        "--time-limit", "60",
        "--pieces", "A=1,B=1,C=1,D=1,E=1,F=1,G=1,H=1,I=1,J=1,K=1,L=1,M=1,N=1,O=1,P=1,Q=1,R=1,S=1,T=1,U=1,V=1,W=1,X=1,Y=1",
        "--max-results", "1000"
    ]
    
    solutions = []
    combinations_tested = 0
    start_time = time.time()
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        for line in process.stdout:
            line = line.strip()
            
            # Track combinations tested
            if "Testing combination" in line and "/" in line:
                try:
                    parts = line.split("Testing combination ")[1].split("/")
                    combinations_tested = int(parts[0])
                except:
                    pass
            
            # Capture solution emissions
            if "DLX DEBUG: Emitting solution" in line:
                solutions.append({
                    "timestamp": time.time() - start_time,
                    "combination_number": combinations_tested
                })
                print(f"Solution #{len(solutions)} found at {time.time() - start_time:.1f}s (combination {combinations_tested})")
            
            # Show progress every 10 seconds
            elapsed = time.time() - start_time
            if elapsed > 0 and int(elapsed) % 10 == 0 and "Time budget:" in line:
                print(f"Progress: {elapsed:.0f}s elapsed, combination {combinations_tested}/12650")
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        process.terminate()
    
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS:")
    print(f"Total runtime: {elapsed_time:.1f} seconds")
    print(f"Combinations tested: {combinations_tested:,} out of 12,650 total")
    print(f"Solutions found: {len(solutions)}")
    print(f"Search progress: {combinations_tested/12650*100:.1f}%")
    
    if solutions:
        print(f"Solution rate: {len(solutions)/elapsed_time*60:.1f} solutions per minute")
        print("\nSolution timeline:")
        for i, sol in enumerate(solutions, 1):
            print(f"  Solution {i}: Found at {sol['timestamp']:.1f}s (combination {sol['combination_number']})")
    else:
        print("No solutions found in the tested combinations")
    
    return solutions, combinations_tested, elapsed_time

def analyze_piece_usage():
    """Run a focused test on known working combinations to analyze piece usage."""
    print("\n" + "=" * 60)
    print("ANALYZING PIECE USAGE FROM KNOWN WORKING COMBINATIONS:")
    print("=" * 60)
    
    # Test some known working combinations from previous runs
    known_combinations = [
        "A=2,E=1,T=1",  # Known working from earlier tests
        "A=1,E=1,O=1,P=1",  # Found in 30-second test
        "A=1,E=1,O=1,Q=1",  # Found in 30-second test
    ]
    
    for i, pieces in enumerate(known_combinations, 1):
        print(f"\nTesting combination {i}: {pieces}")
        
        cmd = [
            sys.executable, "-m", "cli.solve",
            "data/containers/legacy_fixed/16 cell container.json",
            "--engine", "dlx",
            "--seed", "42",
            "--time-limit", "5",
            "--pieces", pieces,
            "--max-results", "10"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            # Count solutions in output
            solution_count = result.stdout.count("DLX DEBUG: Emitting solution")
            print(f"  Solutions found: {solution_count}")
            
            if solution_count > 0:
                print(f"  Pieces used: {pieces}")
                
        except subprocess.TimeoutExpired:
            print(f"  Test timed out")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    # Run the main benchmark
    solutions, combinations, elapsed = run_dlx_benchmark()
    
    # Analyze piece usage patterns
    analyze_piece_usage()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
