#!/usr/bin/env python3
"""
Standalone container validation CLI tool for Ball Puzzle v1.0 containers.

Validates container files against the v1.0 schema and verifies CID computation.
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.io.container import load_container


def validate_single_container(container_path: str, verbose: bool = False) -> bool:
    """
    Validate a single container file.
    
    Returns:
        True if validation passes, False otherwise
    """
    try:
        if verbose:
            print(f"Validating: {container_path}")
        
        container = load_container(container_path)
        
        if verbose:
            print(f"  OK Schema validation passed")
            print(f"  OK Version: {container.get('version')}")
            print(f"  OK Lattice: {container.get('lattice')}")
            print(f"  OK Cells: {len(container.get('cells', []))}")
            print(f"  OK CID: {container.get('cid', 'N/A')[:16]}...")
            if 'designer' in container:
                designer = container['designer']
                print(f"  OK Designer: {designer.get('name')} ({designer.get('date')})")
            print(f"  OK CID computation verified")
        else:
            print(f"OK {container_path}")
        
        return True
        
    except ValueError as e:
        print(f"FAIL {container_path}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"FAIL {container_path}: Failed to load - {e}", file=sys.stderr)
        return False


def find_container_files(directory: str) -> List[str]:
    """Find all .fcc.json files in a directory."""
    path = Path(directory)
    if not path.is_dir():
        raise ValueError(f"Directory not found: {directory}")
    
    containers = list(path.glob("*.fcc.json"))
    if not containers:
        # Also check for .json files as fallback
        containers = list(path.glob("*.json"))
    
    return [str(c) for c in sorted(containers)]


def main():
    parser = argparse.ArgumentParser(
        description="Validate Ball Puzzle v1.0 container files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cli.validate_container container.fcc.json
  python -m cli.validate_container data/containers/v1/ --batch
  python -m cli.validate_container container.fcc.json --verbose
        """
    )
    
    parser.add_argument(
        "path",
        help="Container file or directory path"
    )
    
    parser.add_argument(
        "--batch", "-b",
        action="store_true",
        help="Batch validate all containers in directory"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed validation information"
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if args.batch or path.is_dir():
        # Batch validation
        try:
            container_files = find_container_files(str(path))
            if not container_files:
                print(f"No container files found in: {path}", file=sys.stderr)
                sys.exit(1)
            
            if args.verbose:
                print(f"Found {len(container_files)} container files")
                print()
            
            passed = 0
            failed = 0
            
            for container_file in container_files:
                if validate_single_container(container_file, args.verbose):
                    passed += 1
                else:
                    failed += 1
                
                if args.verbose:
                    print()
            
            print(f"\nValidation Summary:")
            print(f"  Passed: {passed}")
            print(f"  Failed: {failed}")
            print(f"  Total:  {passed + failed}")
            
            if failed > 0:
                sys.exit(1)
            else:
                print("\nOK All containers passed validation")
                
        except Exception as e:
            print(f"Error during batch validation: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        # Single file validation
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            sys.exit(1)
        
        if validate_single_container(str(path), args.verbose):
            if args.verbose:
                print("\nOK Container validation passed")
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
