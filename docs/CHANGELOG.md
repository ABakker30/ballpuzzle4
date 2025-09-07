# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- (planned for M3) Piece inventory support (`piecesUsed` in solutions).
- (planned) CLI options `--inventory` and `--pieces`.

### Changed
- Nothing yet.

### Fixed
- Nothing yet.

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
