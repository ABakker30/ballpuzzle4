# Data Formats

This document describes the main JSON-based data formats used in the Ball Puzzle project.

---

## 1. Container JSON
**Purpose**: Defines the lattice container that pieces must fill.

**Key Fields**
```jsonc
{
  "cid": "CID_hash_string",     // unique container ID
  "cells": 100,                 // number of FCC cells
  "lattice": "fcc",             // lattice type
  "coords": [                   // list of lattice cells (integers)
    {"i":0,"j":0,"k":0},
    {"i":1,"j":0,"k":0}
  ]
}
```

- `cid`: canonical hash (CID) for this container.
- `cells`: total number of valid lattice cells.
- `coords`: integer FCC coordinates for included cells.

---

## 2. Solution JSON
**Purpose**: Captures a complete placement of pieces in a container.

**Key Fields**
```jsonc
{
  "sid": "SID_hash_string",     // unique solution ID
  "cid": "CID_hash_string",     // container reference
  "placements": [
    {"piece":0,"orient":5,"i":0,"j":0,"k":0},
    {"piece":1,"orient":12,"i":2,"j":0,"k":1}
  ]
}
```

- `sid`: canonical hash (SID) for this solution.
- `cid`: container reference (must match).
- `placements`: each placement specifies:
  - `piece`: index in canonical piece library.
  - `orient`: orientation index for that piece.
  - `i,j,k`: integer FCC lattice translation for anchor cell.

---

## 3. Status Snapshot JSON
**Purpose**: Periodic snapshot emitted by engines during search.

**Key Fields**
```jsonc
{
  "v":1,
  "ts_ms":1694281511201,
  "engine":"dfs",
  "run_id":"2025-09-09T19-25Z",
  "container":{"cid":"CID...","cells":100},
  "k":5,
  "nodes":123456,
  "pruned":78901,
  "depth":12,
  "best_depth":17,
  "solutions":0,
  "elapsed_ms":84123,
  "stack":[
    {"piece":3,"orient":42,"i":1,"j":0,"k":-2},
    {"piece":17,"orient":5,"i":2,"j":1,"k":0}
  ],
  "stack_truncated":false,
  "phase":"search"
}
```

- `v`: schema version.
- `ts_ms`: emission timestamp (ms since epoch).
- `engine`: engine name (dfs / dlx / c).
- `run_id`: unique identifier for this run.
- `nodes, pruned, depth, best_depth, solutions`: search metrics.
- `stack`: current placement stack (integers only).
- `stack_truncated`: true if stack was capped.
- `phase`: search phase (init | search | verifying | done).

---

## 4. Events Log (JSONL)
**Purpose**: Detailed chronological trace of engine search.

**Format**: one JSON object per line.

**Examples**
```jsonl
{"t":0.01,"type":"placement","piece":3,"orient":5,"i":1,"j":0,"k":0}
{"t":0.02,"type":"node"}
{"t":0.03,"type":"backtrack"}
{"t":0.05,"type":"solution","sid":"SID_hash"}
{"t":0.06,"type":"done","nodes":1234,"pruned":567,"depth":12}
```

---

## Design Principles
- All FCC coordinates are integers.
- Hashes (CID, SID) uniquely identify containers and solutions.
- Status is for live monitoring; Events is for detailed replay.
- Schema versions are explicit (e.g., `"v":1`).
