# DEPRECATED Legacy Container Directories

⚠️ **These directories contain deprecated container formats and are no longer supported.**

## Deprecated Directories

- `legacy_fixed/` - Legacy container format (pre-v1.0)
- `samples/` - Legacy sample containers (pre-v1.0)

## Migration to v1.0

All containers have been migrated to the v1.0 format in the `v1/` directory:
- Use `data/containers/v1/` for all current containers
- All CLI tools and engines now require v1.0 format only
- Legacy formats will cause validation errors

## What Changed

Legacy format (deprecated):
```json
{
  "name": "Shape 1",
  "lattice_type": "fcc", 
  "coordinates": [[x,y,z], ...]
}
```

v1.0 format (current):
```json
{
  "version": "1.0",
  "lattice": "fcc",
  "cells": [[x,y,z], ...],
  "cid": "sha256:...",
  "designer": {
    "name": "Designer Name",
    "date": "YYYY-MM-DD"
  }
}
```

## Tools for v1.0 Containers

Use these CLI tools for v1.0 containers:
```bash
# Validate containers
python -m cli.validate_container data/containers/v1/ --batch

# Compute/verify CIDs  
python -m cli.compute_cid data/containers/v1/Shape_1.fcc.json --verify

# Solve puzzles
python -m cli.solve data/containers/v1/Shape_1.fcc.json --engine dfs
```

See `data/containers/README.md` for complete v1.0 documentation.
