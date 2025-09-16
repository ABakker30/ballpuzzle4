# Engines Overview: DFS vs DLX

This project ships two production-ready solvers that share the same CLI, schemas, and verification path.

## DFS — Depth-First Search (backtracking)
**Flags:** `--seed`, `--caps-max-nodes`, `--caps-max-depth`  
**Heuristics (opt-in):** `--mrv-pieces`, `--support-bias`

**How it works.** Explores placements recursively with:
- Transposition table (occupancy mask)
- Symmetry breaking (anchor at depth 0)
- Seeded tie-shuffle for deterministic order
- Canonical SID deduplication

**Strengths**
- Flexible; easy to bias with heuristics (support, MRV)
- Streams solutions as they're found
- Bounded via node/depth caps

**When to use**
- Tiny → medium containers (≤ ~32 cells)
- You want first solution quickly and/or incremental streaming

---

## DLX — Algorithm X / Dancing Links (exact cover)
**Flags:** `--caps-max-rows`, `--progress-interval-ms`

**How it works.** Pre-builds feasible placements (rows), enforces:
- One column per container cell (cover exactly once)
- One column per piece *slot* (inventory)
- Symmetry-aware row reduction + dominance pruning

**Strengths**
- Very strong on exact-cover structure
- Smaller search once the rowset is pruned
- Naturally handles inventory constraints

**When to use**
- Small → medium containers where rowset fits in memory
- You want canonical parity with DFS (checked in tests)

---

## Determinism & Identity

Both engines:
- Are deterministic under `--seed`
- Emit schema-validated `events.jsonl` (`snapshot.schema.json`)
- Produce identical canonical SIDs for the same solution
- Are verifiable with `python -m cli.verify`

---

## Quick Guide

- **I want a solution fast** → `--engine dfs` (optionally `--mrv-pieces`, `--support-bias`)  
- **I want stronger combinatorial pruning** → `--engine dlx` (consider `--caps-max-rows`)  
- **I'm not sure** → try both and compare: they share the same CLI and verification path
