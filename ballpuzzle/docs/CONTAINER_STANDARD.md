# Ballpuzzle4 — Container Standard v1.0

This document defines the **only supported JSON format** for containers in Ballpuzzle4.  
All engines, UI, and CLI must read and write this standard exclusively.  
Legacy formats are unsupported.

---

## Required Fields

```json
{
  "version": "1.0",
  "lattice": "fcc",
  "cells": [[x,y,z], ...],
  "cid": "sha256:<64-hex>",
  "designer": {
    "name": "Anton Bakker",
    "date": "2025-09-12",
    "email": "anton@example.com"
  }
}
```

- **version**: "1.0" only.
- **lattice**: "fcc" only (future: "bcc", "sc").
- **cells**: list of integer triplets in engine FCC integer coordinates.
- **cid**: deterministic SHA-256 hash of canonicalized container.
- **designer**:
  - **name** (required): human label.
  - **date** (required): ISO 8601 date string.
  - **email** (optional): contact.

## Canonicalization and CID

See `CANONICALIZATION.md`.

**Summary:**
1. Translate cells so bbox min is [0,0,0].
2. Apply all 24 FCC rotation matrices (no mirrors).
3. For each, re-translate, lexicographically sort.
4. Pick lexicographically smallest list.
5. Serialize `{version,lattice,cells}` with compact JSON.
6. `cid = "sha256:" + sha256_hex(serialized)`.

## File Naming

**Convention**: `<slug>.fcc.json`  
**Example**: `tiny_4.fcc.json`

## Compatibility

- v1.0 is **frozen**.
- Breaking changes require new version (e.g. v2.0).
- No backward compatibility loaders.

## Example

```json
{
  "version": "1.0",
  "lattice": "fcc",
  "cells": [[0,0,0],[1,0,0],[1,1,0],[0,1,0]],
  "cid": "sha256:3a9f5c…",
  "designer": {
    "name": "Anton Bakker",
    "date": "2025-09-12"
  }
}
```
