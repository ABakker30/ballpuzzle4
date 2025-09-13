#!/usr/bin/env python3
"""
[DEPRECATED] Convert legacy container files to Ballpuzzle4 v1.0 standard.

This tool is deprecated as all containers have been migrated to v1.0 format.
Use cli/validate_container.py for v1.0 container validation instead.
"""

import json
import sys
import glob
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import the validator for CID computation
sys.path.append(str(Path(__file__).parent))
from validate_containers import compute_cid

def convert_legacy_container(legacy_path: Path, designer_name: str, designer_email: Optional[str] = None) -> Dict[str, Any]:
    """[DEPRECATED] Convert a legacy container file to v1.0 format.
    
    This function is deprecated. All containers should already be in v1.0 format.
    """
    
    with open(legacy_path, 'r', encoding='utf-8') as f:
        legacy_data = json.load(f)
    
    # Extract coordinates from legacy format
    coordinates = []
    if 'coordinates' in legacy_data:
        coordinates = legacy_data['coordinates']
    elif 'coords' in legacy_data:
        # Handle coords field (if it exists)
        coords_data = legacy_data['coords']
        if isinstance(coords_data, list) and len(coords_data) > 0:
            if isinstance(coords_data[0], dict):
                # Convert from {i,j,k} objects to [i,j,k] arrays
                coordinates = [[cell['i'], cell['j'], cell['k']] for cell in coords_data]
            else:
                coordinates = coords_data
    
    if not coordinates:
        raise ValueError(f"No coordinates found in {legacy_path}")
    
    # Ensure coordinates are in the correct format [i,j,k]
    normalized_coords = []
    for coord in coordinates:
        if isinstance(coord, list) and len(coord) == 3:
            normalized_coords.append([int(coord[0]), int(coord[1]), int(coord[2])])
        elif isinstance(coord, dict) and 'i' in coord and 'j' in coord and 'k' in coord:
            normalized_coords.append([int(coord['i']), int(coord['j']), int(coord['k'])])
        else:
            raise ValueError(f"Invalid coordinate format in {legacy_path}: {coord}")
    
    # Create v1.0 container
    v1_container = {
        "version": "1.0",
        "lattice": "fcc",
        "cells": normalized_coords,
        "cid": "placeholder",  # Will be computed below
        "designer": {
            "name": designer_name,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    }
    
    # Add email if provided
    if designer_email:
        v1_container["designer"]["email"] = designer_email
    
    # Compute the correct CID
    cid = compute_cid(v1_container)
    v1_container["cid"] = cid
    
    return v1_container

def convert_directory(input_dir: Path, output_dir: Path, designer_name: str, designer_email: Optional[str] = None):
    """Convert all JSON files in a directory."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files
    json_files = list(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return
    
    converted_count = 0
    failed_count = 0
    
    for json_file in json_files:
        try:
            print(f"Converting {json_file.name}...")
            
            # Convert to v1.0 format
            v1_container = convert_legacy_container(json_file, designer_name, designer_email)
            
            # Generate output filename
            stem = json_file.stem
            if not stem.endswith('.fcc'):
                stem += '.fcc'
            output_file = output_dir / f"{stem}.json"
            
            # Write v1.0 container
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(v1_container, f, indent=2, ensure_ascii=False)
            
            print(f"  -> {output_file}")
            converted_count += 1
            
        except Exception as e:
            print(f"  X Failed to convert {json_file.name}: {e}")
            failed_count += 1
    
    print(f"\nConversion complete: {converted_count} converted, {failed_count} failed")

def main():
    parser = argparse.ArgumentParser(description="Convert legacy containers to v1.0 standard")
    parser.add_argument("input_dir", help="Directory containing legacy container files")
    parser.add_argument("output_dir", help="Directory to write v1.0 containers")
    parser.add_argument("--designer-name", required=True, help="Designer name for v1.0 containers")
    parser.add_argument("--designer-email", help="Designer email (optional)")
    parser.add_argument("--validate", action="store_true", help="Validate converted containers")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        return 1
    
    print(f"Converting containers from {input_dir} to {output_dir}")
    print(f"Designer: {args.designer_name}")
    if args.designer_email:
        print(f"Email: {args.designer_email}")
    
    convert_directory(input_dir, output_dir, args.designer_name, args.designer_email)
    
    if args.validate:
        print("\nValidating converted containers...")
        # Import and run validator
        from validate_containers import validate_file
        
        v1_files = list(output_dir.glob("*.json"))
        valid_count = 0
        
        for v1_file in v1_files:
            if validate_file(v1_file):
                valid_count += 1
                print(f"  OK {v1_file.name}")
            else:
                print(f"  FAIL {v1_file.name}")
        
        print(f"\nValidation: {valid_count}/{len(v1_files)} containers valid")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
