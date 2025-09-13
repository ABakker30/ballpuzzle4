# Containers

- **v1/** — Container Standard v1.0 compliant containers (current format)
- **examples/** — Golden example containers for testing and validation
- **legacy_fixed/** — Legacy containers (deprecated, use v1/ instead)
- **samples/** — Legacy samples (deprecated, use v1/ instead)

## Container Standard v1.0

All containers now follow the v1.0 standard format:
```json
{
  "version": "1.0",
  "lattice": "fcc",
  "cells": [[x,y,z], ...],
  "cid": "sha256:...",
  "designer": {
    "name": "Anton Bakker",
    "date": "2025-09-12"
  }
}
```

## Usage

Solve any v1.0 container with the CLI:
```bash
python -m cli.solve data/containers/v1/Shape_1.fcc.json --engine dfs --pieces A=25
```

Verify solutions:
```bash
python -m cli.verify solution.json data/containers/v1/Shape_1.fcc.json
```

Validate containers:
```bash
python tools/validate_containers.py data/containers/v1/
```
