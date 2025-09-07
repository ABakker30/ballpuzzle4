# Roadmap

This roadmap defines the near-term milestones for **ballpuzzle4**.  
Each milestone is deliberately small in scope to keep the project clean and on track.  
When a milestone is completed, it is tagged (v0.x.0) and logged in `CHANGELOG.md`.

---

## ✅ Completed

### M1 — Contracts & FCC engine-first
- [x] Add FCC lattice canonicalization (`coords/canonical.py`) with `cid_sha256`.
- [x] Add FCC neighbor set (`coords/lattice_fcc.py`).
- [x] Define JSON schema for container (`container.schema.json`).
- [x] Add golden tests for CID invariance.
- [x] Add CI workflow (`.github/workflows/ci.yml`).
- [x] Create ADR 0001: Engine-native FCC, convert only at edges.
- **Tag:** v0.1.0

### M2 — Engine registry, CLI wiring, schemas, reporting
- [x] Add engine registry with pluggable `current` and `dfs` engines.
- [x] Stub engine implementations that emit `tick/solution/done` events.
- [x] Add CLI (`cli/solve.py`) to run engines and write `events.jsonl` and `solution.json`.
- [x] Add minimal `solution.schema.json` with required fields.
- [x] Add reporting: basic TTY and JSONL writer.
- [x] Add end-to-end test `test_cli_wire.py`.
- [x] Add `.gitignore`, `.editorconfig`, `CHANGELOG.md`.
- **Tag:** v0.2.0

---

## 🚧 Upcoming

### M3 — Piece inventory & solutions
- [ ] Implement `PieceBag` (multiset of pieces with counts).
- [ ] Support `--inventory inventory.json` and `--pieces A=1,B=2,...`.
- [ ] Include `piecesUsed` in solutions.
- [ ] Expand `inventory.schema.json` and update `solution.schema.json`.
- [ ] Add test: CLI run with inventory; assert solution JSON contains correct `piecesUsed`.
- **Planned Tag:** v0.3.0

### M4 — Symmetry & small-container mode
- [x] Implement container symmetry group (24 rotations).
- [x] Add anchor rule (canonical placement).
- [x] Add transposition table (mask keyed).
- [x] Enable tie-shuffle in small-container mode (|cells| ≤ 32).
- [x] Add tests: no rotated duplicate solutions; node count reduction.
- **Completed Tag:** v0.4.0

### M4.5 — Surface Small-Container Mode (completed)
- [x] Expose symmetry-group size, small-container flag, seed, and TT presence in event log.
- [x] Add visibility fields without changing search behavior.
- **Completed Tag:** v0.4.1

### M5 — Minimal DFS Engine (completed)
- [x] Implement real DFS engine using TT, tie-shuffle, and anchor rule.
- [x] Prove control-flow and determinism with synthetic placements.
- [x] Add comprehensive tests for DFS scaffold and deterministic behavior.
- **Completed Tag:** v0.5.0

### M6 — Documentation & release polish
- [ ] Expand `ENGINE_OVERVIEW.md` with diagrams and examples.
- [ ] Add ADRs for: engine API, inventory, symmetry-breaking.
- [ ] Update `CHANGELOG.md` and `ROADMAP.md`.
- [ ] Tag stable `v1.0.0` milestone.


How to use
Keep this short and milestone-focused.
When you complete a task, tick [ ] → [x].
At milestone close: cut a tag, update CHANGELOG.md, move it into the ✅ Completed section.
