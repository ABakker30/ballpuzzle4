#!/usr/bin/env python3
import sys
import subprocess
import time
import signal
import os

def run_with_timeout(cmd, timeout_seconds):
    """Run a command with a hard timeout"""
    print(f"Running: {' '.join(cmd)}")
    print(f"Timeout: {timeout_seconds} seconds")
    
    start_time = time.time()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        elapsed = time.time() - start_time
        print(f"Process completed in {elapsed:.2f} seconds")
        print(f"Exit code: {process.returncode}")
        if stdout:
            print("STDOUT:")
            print(stdout)
        if stderr:
            print("STDERR:")
            print(stderr)
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"Process timed out after {elapsed:.2f} seconds - killing it")
        process.kill()
        try:
            stdout, stderr = process.communicate(timeout=2)
            if stdout:
                print("STDOUT (partial):")
                print(stdout)
            if stderr:
                print("STDERR (partial):")
                print(stderr)
        except:
            pass
        print("Process was killed due to timeout")

if __name__ == "__main__":
    cmd = [
        sys.executable, "-m", "cli.solve",
        "data/containers/legacy_fixed/Shape_3.json",
        "--engine", "dfs",
        "--time-limit", "10",
        "--max-results", "1",
        "--pieces", "A=1,B=1,C=1,D=1,E=1,F=1,G=1,H=1,I=1,J=1,K=1,L=1,M=1,N=1,O=1,P=1,Q=1,R=1,S=1,T=1,U=1,V=1,W=1,X=1,Y=1"
    ]
    
    run_with_timeout(cmd, 12)  # 12 second hard timeout
