# Ball Puzzle Containers

## Current Format (v1.0)

- **v1/** — Container Standard v1.0 compliant containers (current format)
- All containers use `.fcc.json` extension
- Legacy formats are deprecated and no longer supported

## Container Standard v1.0 Format

All containers follow the strict v1.0 standard:
```json
{
  "version": "1.0",
  "lattice": "fcc",
  "cells": [[x,y,z], ...],
  "cid": "sha256:...",
  "designer": {
    "name": "Designer Name",
    "date": "YYYY-MM-DD",
    "email": "optional@example.com"
  }
}
```

### Key Features:
- **version**: Always "1.0"
- **lattice**: Always "fcc" (face-centered cubic)
- **cells**: Array of [i,j,k] integer coordinates in FCC lattice
- **cid**: Content identifier with sha256: prefix using FCC canonicalization
- **designer**: Metadata about container creator

## CLI Usage

### Solve Puzzles
```bash
python -m cli.solve data/containers/v1/Shape_1.fcc.json --engine dfs --pieces A=25
python -m cli.solve data/containers/v1/Shape_3.fcc.json --engine dlx --time-limit 60
```

### Verify Solutions
```bash
python -m cli.verify solution.json data/containers/v1/Shape_1.fcc.json
```

### Validate Containers
```bash
# Single container
python -m cli.validate_container data/containers/v1/Shape_1.fcc.json --verbose

# Batch validation
python -m cli.validate_container data/containers/v1/ --batch
```

### Compute CIDs
```bash
# Compute CID for container
python -m cli.compute_cid data/containers/v1/Shape_1.fcc.json

# Verify stored CID matches computed CID
python -m cli.compute_cid data/containers/v1/Shape_1.fcc.json --verify
```

## Available Containers

The v1/ directory contains 29 validated containers:
- Shape_1 through Shape_24 (various sizes and complexities)
- Specialized containers: 16-cell, 40-cell, hollow pyramid, test containers
- All containers have verified CIDs and proper v1.0 format

## Legacy Containers (Deprecated)

**⚠️ DEPRECATED**: Legacy container formats are no longer supported:
- `legacy_fixed/` - Old format containers (use v1/ equivalents)
- `samples/` - Legacy samples (use v1/ equivalents)

All CLI tools and engines now require v1.0 format containers only.
