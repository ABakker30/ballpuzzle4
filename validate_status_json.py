#!/usr/bin/env python3
"""
Validate status snapshot JSON files against the schema.
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Installing jsonschema package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema"])
    import jsonschema

def validate_status_json(json_file: str, schema_file: str) -> bool:
    """Validate a status JSON file against the schema."""
    try:
        # Load schema
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        
        # Load JSON data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Validate
        jsonschema.validate(data, schema)
        print(f"[PASS] {json_file} is valid against schema")
        return True
        
    except jsonschema.ValidationError as e:
        print(f"[FAIL] {json_file} validation failed:")
        print(f"  Error: {e.message}")
        print(f"  Path: {' -> '.join(str(p) for p in e.absolute_path)}")
        return False
        
    except Exception as e:
        print(f"[ERROR] Error validating {json_file}: {e}")
        return False

def main():
    schema_file = "docs/schemas/status_snapshot.v1.json"
    
    # Test files to validate
    test_files = [
        "status_test_dfs.json",
        "status_test_dlx.json"
    ]
    
    all_valid = True
    
    for test_file in test_files:
        if Path(test_file).exists():
            valid = validate_status_json(test_file, schema_file)
            all_valid = all_valid and valid
        else:
            print(f"[SKIP] {test_file} not found, skipping")
    
    if all_valid:
        print("\n[SUCCESS] All status JSON files are valid!")
        sys.exit(0)
    else:
        print("\n[FAILED] Some status JSON files failed validation")
        sys.exit(1)

if __name__ == "__main__":
    main()
