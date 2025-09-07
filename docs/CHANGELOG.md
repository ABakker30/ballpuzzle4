# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- (planned for M7) Future enhancements and optimizations.

### Changed
- Nothing yet.

### Fixed
- Nothing yet.

---

## [0.6.0] - 2025-09-07
### Added
- **M6**: Canonical solution identity and deduplication under container symmetry.
- `src/io/solution_sig.py` with `canonical_state_signature()` function for SHA256-based state hashing.
- Solution deduplication in both `current_engine.py` and `dfs_engine.py` to prevent rotated duplicates.
- `sid_state_canon_sha256` field in solution JSON for canonical state identification.
- Tests for canonical signature behavior and engine deduplication (`test_solution_canonical_sig.py`, `test_engine_emits_unique_solutions.py`).
- Documentation section on canonical solution identity in `ENGINE_OVERVIEW.md`.

### Changed
- Engines now track emitted solution signatures and skip duplicates before emission.
- Solution count metrics reflect actual unique solutions emitted after deduplication.

---

## [0.5.0] - 2025-09-07
### Added
- **M5**: Minimal DFS engine using M4 utilities (`src/solver/engines/dfs_engine.py`).
- Real DFS with transposition table pruning, anchor rule filtering, and tie-shuffle.
- Synthetic placements proving control-flow and determinism.
- Tests for DFS scaffold runs and deterministic behavior.

### Changed
- Updated ROADMAP.md to reflect M4, M4.5, and M5 completion.

---

## [0.4.1] - 2025-09-07
### Added
- **M4.5**: Small-container mode visibility in event logs.
- Exposed symmetry group size, small-mode flag, seed, and TT presence.
- Test for small-mode field visibility (`tests/test_smallmode_visibility.py`).

### Changed
- Updated `current_engine.py` to surface M4 utility metrics without behavior change.

---

## [0.4.0] - 2025-09-07
### Added
- **M4**: Complete symmetry utilities for small-container mode.
- FCC lattice symmetry with 24 proper rotations (`src/coords/symmetry_fcc.py`).
- Symmetry breaking with anchor rule (`src/solver/symbreak.py`).
- Occupancy masks and transposition table (`src/solver/tt.py`).
- Seeded tie-shuffle for deterministic randomness (`src/solver/heuristics.py`).
- Comprehensive test suite with 30 passing tests across 4 test files.

### Changed
- All utilities operate on FCC lattice integer coordinates (no world-space math).

---

## [0.3.0] - 2025-09-07
### Added
- **M3**: Piece inventory and solution tracking.
- `PieceBag` class for multiset piece inventory (`src/pieces/inventory.py`).
- CLI support for `--inventory` JSON files and `--pieces` inline format.
- `piecesUsed` field in solution JSON output.
- JSON schema validation for inventory files.
- End-to-end tests for inventory wire-through.

### Changed
- Enhanced CLI with inventory options and precedence rules.
- Updated solution schema to include `piecesUsed` field.

---

## [0.2.0] - 2025-09-07
### Added
- Engine registry with pluggable `current` and `dfs` engines.
- CLI solver command (`cli/solve.py`) that runs engines, writes `events.jsonl` and `solution.json`.
- Minimal `solution.schema.json` with required fields.
- Event log writer (`snapshot.py`) and solution writer (`solution.py`).
- Reporting: basic TTY exporter.
- End-to-end test `test_cli_wire.py`.

### Changed
- Scope reduced to minimal M2 wiring (old tests for removed features now obsolete).

### Fixed
- Enforced engine-only FCC integers throughout core; no world-space math leaks.

---

## [0.1.0] - 2025-09-07
### Added
- Initial repo scaffold.
- FCC lattice canonicalization (`coords/canonical.py`) with `cid_sha256`.
- FCC neighbor set (`coords/lattice_fcc.py`).
- JSON schema for container (`container.schema.json`).
- Golden test for CID invariance.
- ADR 0001: Engine-native FCC, convert only at edges.
- CI workflow (`.github/workflows/ci.yml`).
