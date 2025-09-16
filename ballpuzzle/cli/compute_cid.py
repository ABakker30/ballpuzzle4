#!/usr/bin/env python3
"""
CID computation CLI utility for Ball Puzzle v1.0 containers.

Computes and displays CID for container files, with options to verify existing CIDs.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def compute_cid_fcc(cells: List[tuple]) -> str:
    """Compute CID using exact same algorithm as UI."""
    import hashlib
    
    # Convert to list format for canonicalization
    cells_list = [[int(c[0]), int(c[1]), int(c[2])] for c in cells]
    
    # Apply same canonicalization as UI
    canonical_cells = canonicalize_cells_ui(cells_list)
    
    # Create payload matching UI format exactly
    payload = {
        'version': '1.0',
        'lattice': 'fcc',
        'cells': canonical_cells
    }
    
    # Serialize with same format as UI (JSON.stringify with null, 0)
    serialized = json.dumps(payload, separators=(',', ':'))
    
    # Compute SHA-256 hash
    hash_bytes = hashlib.sha256(serialized.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()
    
    return f"sha256:{hash_hex}"


def normalize_translation(cells):
    """Translate cells to origin (same as UI)."""
    if not cells:
        return cells
    
    # Find minimum coordinates
    min_coords = [float('inf')] * 3
    for cell in cells:
        for i in range(3):
            min_coords[i] = min(min_coords[i], cell[i])
    
    # Translate to origin
    return [[cell[0] - min_coords[0], cell[1] - min_coords[1], cell[2] - min_coords[2]] for cell in cells]


def apply_rotation(cells, rotation):
    """Apply rotation matrix to cells (same as UI)."""
    result = []
    for cell in cells:
        new_cell = [
            rotation[0][0] * cell[0] + rotation[0][1] * cell[1] + rotation[0][2] * cell[2],
            rotation[1][0] * cell[0] + rotation[1][1] * cell[1] + rotation[1][2] * cell[2],
            rotation[2][0] * cell[0] + rotation[2][1] * cell[1] + rotation[2][2] * cell[2]
        ]
        result.append(new_cell)
    return result


def canonicalize_cells_ui(cells):
    """Canonicalize cells using exact same algorithm as UI."""
    if not cells:
        return cells
    
    # FCC rotation matrices (same as UI)
    FCC_ROTATIONS = [
        [[1, 0, 0], [0, 1, 0], [0, 0, 1]],    # Identity
        [[1, 0, 0], [0, 0, -1], [0, 1, 0]],   # 90° around X
        [[1, 0, 0], [0, -1, 0], [0, 0, -1]],  # 180° around X
        [[1, 0, 0], [0, 0, 1], [0, -1, 0]],   # 270° around X
        [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],   # 90° around Y
        [[-1, 0, 0], [0, 1, 0], [0, 0, -1]],  # 180° around Y
        [[0, 0, -1], [0, 1, 0], [1, 0, 0]],   # 270° around Y
        [[0, -1, 0], [1, 0, 0], [0, 0, 1]],   # 90° around Z
        [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],  # 180° around Z
        [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],   # 270° around Z
        [[0, 1, 0], [0, 0, 1], [1, 0, 0]],    # 120° [1,1,1]
        [[0, 0, 1], [1, 0, 0], [0, 1, 0]],    # 240° [1,1,1]
        [[0, 0, -1], [1, 0, 0], [0, -1, 0]],  # 120° [1,1,-1]
        [[0, -1, 0], [0, 0, -1], [1, 0, 0]],  # 240° [1,1,-1]
        [[0, 0, 1], [-1, 0, 0], [0, -1, 0]],  # 120° [1,-1,1]
        [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],  # 240° [1,-1,1]
        [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],  # 120° [-1,1,1]
        [[0, 1, 0], [0, 0, -1], [-1, 0, 0]],  # 240° [-1,1,1]
        [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],   # 90° around [1,1,0]
        [[0, 0, 1], [0, -1, 0], [1, 0, 0]],   # 90° around [1,-1,0]
        [[0, 0, -1], [0, -1, 0], [-1, 0, 0]], # 90° around [-1,-1,0]
        [[-1, 0, 0], [0, 0, -1], [0, -1, 0]], # 90° around [-1,1,0]
        [[0, -1, 0], [-1, 0, 0], [0, 0, -1]], # 90° around [1,0,1]
        [[0, 1, 0], [1, 0, 0], [0, 0, -1]],   # 90° around [-1,0,1]
    ]
    
    normalized = normalize_translation(cells)
    candidates = []
    
    # Apply all 24 FCC rotations
    for rotation in FCC_ROTATIONS:
        rotated = apply_rotation(normalized, rotation)
        renormalized = normalize_translation(rotated)
        # Sort lexicographically
        sorted_cells = sorted(renormalized, key=lambda cell: (cell[0], cell[1], cell[2]))
        candidates.append(sorted_cells)
    
    # Return lexicographically smallest candidate
    def compare_arrays(a, b):
        for i in range(min(len(a), len(b))):
            for j in range(3):
                if a[i][j] != b[i][j]:
                    return a[i][j] - b[i][j]
        return len(a) - len(b)
    
    min_candidate = candidates[0]
    for candidate in candidates[1:]:
        if compare_arrays(candidate, min_candidate) < 0:
            min_candidate = candidate
    
    return min_candidate


def load_container_raw(path: str) -> Dict[str, Any]:
    """Load container file without validation for CID computation."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def compute_container_cid(container_path: str, verify: bool = False, verbose: bool = False) -> bool:
    """
    Compute CID for a container file.
    
    Args:
        container_path: Path to container file
        verify: If True, compare with existing CID in file
        verbose: Show detailed information
    
    Returns:
        True if successful (and CID matches if verify=True), False otherwise
    """
    try:
        container = load_container_raw(container_path)
        
        # Extract cells from either v1.0 format (cells) or legacy format (coordinates)
        if "cells" in container:
            cells_data = container["cells"]
            format_type = "v1.0"
        elif "coordinates" in container:
            cells_data = container["coordinates"]
            format_type = "legacy"
        else:
            print(f"✗ {container_path}: No cells or coordinates field found", file=sys.stderr)
            return False
        
        # Convert to tuples and compute CID using FCC canonicalization (same as UI)
        cells = [tuple(map(int, c)) for c in cells_data]
        computed_cid = compute_cid_fcc(cells)
        
        if verbose:
            print(f"File: {container_path}")
            print(f"Format: {format_type}")
            print(f"Cells: {len(cells)}")
            print(f"Computed CID: {computed_cid}")
        else:
            print(f"{computed_cid}  {container_path}")
        
        if verify:
            stored_cid = container.get("cid")
            if stored_cid:
                if stored_cid == computed_cid:
                    if verbose:
                        print(f"OK CID matches stored value")
                    return True
                else:
                    if verbose:
                        print(f"FAIL CID mismatch!")
                        print(f"  Stored:   {stored_cid}")
                        print(f"  Computed: {computed_cid}")
                    else:
                        print(f"FAIL CID mismatch in {container_path}", file=sys.stderr)
                        print(f"  Stored:   {stored_cid}", file=sys.stderr)
                        print(f"  Computed: {computed_cid}", file=sys.stderr)
                    return False
            else:
                if verbose:
                    print(f"WARN No stored CID found in file")
                else:
                    print(f"WARN No CID in {container_path}", file=sys.stderr)
                return True
        
        return True
        
    except Exception as e:
        print(f"FAIL {container_path}: {e}", file=sys.stderr)
        return False


def find_container_files(directory: str) -> List[str]:
    """Find all container files in a directory."""
    path = Path(directory)
    if not path.is_dir():
        raise ValueError(f"Directory not found: {directory}")
    
    # Look for .fcc.json files first, then .json files
    containers = list(path.glob("*.fcc.json"))
    if not containers:
        containers = list(path.glob("*.json"))
    
    return [str(c) for c in sorted(containers)]


def main():
    parser = argparse.ArgumentParser(
        description="Compute CID for Ball Puzzle container files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cli.compute_cid container.fcc.json
  python -m cli.compute_cid container.fcc.json --verify
  python -m cli.compute_cid data/containers/v1/ --batch --verify
  python -m cli.compute_cid container.fcc.json --verbose
        """
    )
    
    parser.add_argument(
        "path",
        help="Container file or directory path"
    )
    
    parser.add_argument(
        "--batch", "-b",
        action="store_true",
        help="Process all containers in directory"
    )
    
    parser.add_argument(
        "--verify", "-c",
        action="store_true",
        help="Verify CID matches stored value in file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed information"
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if args.batch or path.is_dir():
        # Batch processing
        try:
            container_files = find_container_files(str(path))
            if not container_files:
                print(f"No container files found in: {path}", file=sys.stderr)
                sys.exit(1)
            
            if args.verbose:
                print(f"Processing {len(container_files)} container files")
                print()
            
            success_count = 0
            total_count = len(container_files)
            
            for container_file in container_files:
                if compute_container_cid(container_file, args.verify, args.verbose):
                    success_count += 1
                
                if args.verbose:
                    print()
            
            if args.verify:
                failed_count = total_count - success_count
                if args.verbose:
                    print(f"CID Verification Summary:")
                    print(f"  Passed: {success_count}")
                    print(f"  Failed: {failed_count}")
                    print(f"  Total:  {total_count}")
                
                if failed_count > 0:
                    sys.exit(1)
                elif args.verbose:
                    print("\nOK All CIDs verified successfully")
                
        except Exception as e:
            print(f"Error during batch processing: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        # Single file processing
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(1)
        
        if compute_container_cid(str(path), args.verify, args.verbose):
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
