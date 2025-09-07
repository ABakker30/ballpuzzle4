#!/usr/bin/env python3
"""
Batch-convert legacy FCC container JSONs to the current schema.

What it does:
- Reads *.json files (optionally recursively)
- Normalizes to { "name": "...", "lattice_type": "fcc", "coordinates": [...] }
- Writes to --out (mirrors directory structure) OR in-place with .bak backups
- Optional JSON Schema validation against src/io/schema/container.schema.json

Usage examples:
  # Dry-run to see what would change
  python -m scripts.convert_legacy_containers --src legacy_dir --dry-run

  # Convert into a separate output folder (recommended)
  python -m scripts.convert_legacy_containers --src legacy_dir --out fixed_dir

  # Convert in place (creates .bak once per file)
  python -m scripts.convert_legacy_containers --src legacy_dir --inplace

  # Recurse subdirectories and validate output against schema
  python -m scripts.convert_legacy_containers --src legacy_dir --out fixed_dir --recursive --validate
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Optional schema validation (enabled with --validate).
# We import lazily so the script still works if jsonschema isn't installed.
def _try_load_schema():
    try:
        from src.io.schema import load_schema  # repo-local
        from jsonschema import validate
        return load_schema("container.schema.json"), validate
    except Exception:
        return None, None

def _normalize_container(data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """Convert legacy container format to current schema format."""
    # Extract lattice type
    lattice = str(data.get("lattice", data.get("lattice_type", "fcc"))).lower()
    
    # Extract coordinates/cells
    coordinates = data.get("coordinates", data.get("cells", []))
    
    # Normalize coordinates to int triples
    norm_coords: List[List[int]] = []
    for c in coordinates:
        if isinstance(c, (list, tuple)) and len(c) == 3:
            x, y, z = c
            norm_coords.append([int(x), int(y), int(z)])
        else:
            raise ValueError(f"Invalid coordinate entry: {c!r}")
    
    # Generate name from filename if not present
    name = data.get("name", Path(filename).stem)
    
    return {
        "name": name,
        "lattice_type": lattice,
        "coordinates": norm_coords
    }

def _relpath(base: Path, p: Path) -> Path:
    try:
        return p.relative_to(base)
    except Exception:
        return p.name

def convert_one(src_file: Path, out_file: Path, validate_out: bool, schema_ctx: Tuple[Any, Any] | None):
    raw = json.loads(src_file.read_text(encoding="utf-8"))
    new_obj = _normalize_container(raw, src_file.name)

    # Validation if requested and available
    if validate_out and schema_ctx is not None:
        schema, validate = schema_ctx
        if schema and validate:
            validate(instance=new_obj, schema=schema)

    # Ensure parent
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(new_obj, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Source directory containing legacy .json containers")
    ap.add_argument("--out", help="Output directory; if omitted and --inplace is set, converts in place")
    ap.add_argument("--inplace", action="store_true", help="Convert files in place (writes .bak once)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subdirectories")
    ap.add_argument("--dry-run", action="store_true", help="Only report what would be done")
    ap.add_argument("--validate", action="store_true", help="Validate outputs against current container schema")
    ap.add_argument("--pattern", default="*.json", help="Glob pattern (default: *.json)")
    args = ap.parse_args()

    src_root = Path(args.src).resolve()
    if not src_root.exists():
        print(f"[ERROR] Source path not found: {src_root}", file=sys.stderr)
        sys.exit(2)

    if args.out and args.inplace:
        print("[ERROR] Use either --out or --inplace, not both.", file=sys.stderr)
        sys.exit(2)

    if not args.out and not args.inplace:
        print("[ERROR] Specify either --out or --inplace", file=sys.stderr)
        sys.exit(2)

    schema_ctx = None
    if args.validate:
        schema_ctx = _try_load_schema()
        if schema_ctx == (None, None):
            print("[WARN] Validation requested but jsonschema or schema loader not available; proceeding without validation.", file=sys.stderr)

    # Discover files
    files: List[Path] = []
    if args.recursive:
        files = list(src_root.rglob(args.pattern))
    else:
        files = list(src_root.glob(args.pattern))

    if not files:
        print("[INFO] No files matched.")
        return

    print(f"[INFO] Found {len(files)} JSON file(s).")
    for src_file in files:
        try:
            rel = _relpath(src_root, src_file)
            if args.out:
                dst = Path(args.out).resolve() / rel
            else:
                # In-place: write to same directory, overwriting original (with .bak once)
                dst = src_file

            # Plan actions
            if args.dry_run:
                # Peek & show normalization result lattice/coordinate count
                try:
                    raw = json.loads(src_file.read_text(encoding="utf-8"))
                    norm = _normalize_container(raw, src_file.name)
                    print(f"[DRY] {src_file} -> {dst}  lattice_type={norm.get('lattice_type')}  coordinates={len(norm.get('coordinates',[]))}")
                except Exception as e:
                    print(f"[DRY][ERROR] {src_file}: {e}")
                continue

            if args.inplace:
                bak = src_file.with_suffix(src_file.suffix + ".bak")
                # Create backup once
                if not bak.exists():
                    shutil.copy2(src_file, bak)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)

            convert_one(src_file, dst, args.validate, schema_ctx)
            print(f"[OK] {src_file} -> {dst}")

        except Exception as e:
            print(f"[ERROR] {src_file}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
