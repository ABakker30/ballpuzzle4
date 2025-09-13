#!/usr/bin/env python3
"""
Container validation tool for Ballpuzzle4 v1.0 standard.
Validates JSON schema and recomputes CID to ensure correctness.
"""

import json
import sys
import glob
import hashlib
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Any

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("Error: jsonschema package required. Install with: pip install jsonschema")
    sys.exit(1)

# Load schema
SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "container.schema.json"
if not SCHEMA_PATH.exists():
    print(f"Error: Schema not found at {SCHEMA_PATH}")
    sys.exit(1)

with open(SCHEMA_PATH, encoding="utf-8") as f:
    SCHEMA = json.load(f)

validator = Draft7Validator(SCHEMA)

# FCC rotation matrices (24 proper rotations, det=+1)
FCC_ROTATIONS = [
    # Identity
    [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    
    # Face rotations around X-axis
    [[1, 0, 0], [0, 0, -1], [0, 1, 0]],   # 90°
    [[1, 0, 0], [0, -1, 0], [0, 0, -1]],  # 180°
    [[1, 0, 0], [0, 0, 1], [0, -1, 0]],   # 270°
    
    # Face rotations around Y-axis
    [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],   # 90°
    [[-1, 0, 0], [0, 1, 0], [0, 0, -1]],  # 180°
    [[0, 0, -1], [0, 1, 0], [1, 0, 0]],   # 270°
    
    # Face rotations around Z-axis
    [[0, -1, 0], [1, 0, 0], [0, 0, 1]],   # 90°
    [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],  # 180°
    [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],   # 270°
    
    # Edge rotations (180° around edges)
    [[0, 1, 0], [1, 0, 0], [0, 0, -1]],   # [1,1,0]
    [[0, -1, 0], [-1, 0, 0], [0, 0, -1]], # [1,-1,0]
    [[0, 0, 1], [0, -1, 0], [1, 0, 0]],   # [1,0,1]
    [[0, 0, -1], [0, -1, 0], [-1, 0, 0]], # [1,0,-1]
    [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],   # [0,1,1]
    [[-1, 0, 0], [0, 0, -1], [0, -1, 0]], # [0,1,-1]
    
    # Vertex rotations (120° and 240° around body diagonals)
    [[0, 0, 1], [1, 0, 0], [0, 1, 0]],    # 120° [1,1,1]
    [[0, 1, 0], [0, 0, 1], [1, 0, 0]],    # 240° [1,1,1]
    [[0, 0, -1], [1, 0, 0], [0, -1, 0]],  # 120° [1,1,-1]
    [[0, -1, 0], [0, 0, -1], [1, 0, 0]],  # 240° [1,1,-1]
    [[0, 0, 1], [-1, 0, 0], [0, -1, 0]],  # 120° [1,-1,1]
    [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],  # 240° [1,-1,1]
    [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],  # 120° [-1,1,1]
    [[0, 1, 0], [0, 0, -1], [-1, 0, 0]],  # 240° [-1,1,1]
]

def apply_rotation(cells: List[List[int]], rotation: List[List[int]]) -> List[List[int]]:
    """Apply rotation matrix to list of cells."""
    result = []
    for cell in cells:
        x, y, z = cell
        new_x = rotation[0][0] * x + rotation[0][1] * y + rotation[0][2] * z
        new_y = rotation[1][0] * x + rotation[1][1] * y + rotation[1][2] * z
        new_z = rotation[2][0] * x + rotation[2][1] * y + rotation[2][2] * z
        result.append([new_x, new_y, new_z])
    return result

def normalize_translation(cells: List[List[int]]) -> List[List[int]]:
    """Translate cells so bounding box minimum is at [0,0,0]."""
    if not cells:
        return cells
    
    xs, ys, zs = zip(*cells)
    min_x, min_y, min_z = min(xs), min(ys), min(zs)
    
    return [[x - min_x, y - min_y, z - min_z] for x, y, z in cells]

def canonicalize(cells: List[List[int]]) -> List[List[int]]:
    """
    Compute canonical form of cells using FCC rotations.
    Returns lexicographically smallest normalized and sorted cell list.
    """
    if not cells:
        return cells
    
    # Start with normalized translation
    normalized = normalize_translation(cells)
    candidates = []
    
    # Apply all 24 FCC rotations
    for rotation in FCC_ROTATIONS:
        rotated = apply_rotation(normalized, rotation)
        renormalized = normalize_translation(rotated)
        sorted_cells = sorted(renormalized)
        candidates.append(sorted_cells)
    
    # Return lexicographically smallest candidate
    return min(candidates)

def compute_cid(obj: Dict[str, Any]) -> str:
    """Compute CID from container object."""
    canon_cells = canonicalize(obj["cells"])
    payload = {
        "version": obj["version"],
        "lattice": obj["lattice"],
        "cells": canon_cells
    }
    serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    hash_hex = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"sha256:{hash_hex}"

def validate_file(path: Path) -> bool:
    """Validate a single container file. Returns True if valid."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[JSON FAIL] {path}: {e}")
        return False
    except Exception as e:
        print(f"[READ FAIL] {path}: {e}")
        return False
    
    # Schema validation
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        print(f"[SCHEMA FAIL] {path}")
        for error in errors:
            path_str = ".".join(str(p) for p in error.path) if error.path else "root"
            print(f"  - {path_str}: {error.message}")
        return False
    
    # CID validation
    try:
        recomputed_cid = compute_cid(data)
        if recomputed_cid != data["cid"]:
            print(f"[CID FAIL] {path}")
            print(f"  expected: {data['cid']}")
            print(f"  computed: {recomputed_cid}")
            return False
    except Exception as e:
        print(f"[CID ERROR] {path}: {e}")
        return False
    
    return True

def find_container_files() -> List[Path]:
    """Find all container JSON files in standard locations."""
    patterns = [
        "examples/containers/**/*.json",
        "tests/data/containers/**/*.json",
        "data/containers/**/*.json",
        "data/containers/**/*.fcc.json"
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern, recursive=True))
    
    return [Path(f) for f in files if f.endswith('.json')]

def main():
    parser = argparse.ArgumentParser(description="Validate Ballpuzzle4 v1.0 containers")
    parser.add_argument("files", nargs="*", help="Container files to validate (default: auto-discover)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        files = find_container_files()
    
    if not files:
        print("No container files found to validate")
        return 0
    
    if args.verbose:
        print(f"Validating {len(files)} files...")
    
    valid_count = 0
    for file_path in files:
        if not file_path.exists():
            print(f"[NOT FOUND] {file_path}")
            continue
            
        if validate_file(file_path):
            valid_count += 1
            if args.verbose:
                print(f"[OK] {file_path}")
    
    invalid_count = len([f for f in files if f.exists()]) - valid_count
    
    if args.verbose or invalid_count > 0:
        print(f"\nResults: {valid_count} valid, {invalid_count} invalid")
    
    return 0 if invalid_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
