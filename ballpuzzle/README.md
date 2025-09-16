# Ballpuzzle Solver

Engine-native FCC solver for lattice puzzles using A–Y pieces.  
Features both DFS and DLX engines, schema-validated event logs, and canonical solution verification.

See [UI Design Specification](docs/ui_design.md) for planned features.

## Quickstart

Install requirements (Python 3.10+):

```bash
pip install -r requirements.txt
```

Solve a container:
```bash
python -m cli.solve tests/data/containers/tiny_4.fcc.json \
  --engine engine-c \
  --pieces A=1 \
  --eventlog out/events.jsonl \
  --solution out/solution.json
```

Verify a solution:
```bash
python -m cli.verify out/solution.json tests/data/containers/tiny_4.fcc.json
```

Exit codes: 0 = valid, 2 = invalid.  
See [docs/VERIFY.md](docs/VERIFY.md) for full details.

## Engines

**DFS**: depth-first with caps, heuristics, TT, dedup.  
**DLX**: Algorithm X exact cover with row reduction, dominance pruning, canonical dedup.  
**Engine-C**: high-performance FCC solver with holes-first ordering, disconnected void pruning, and bitset operations.

All engines emit schema-validated JSONL logs (`snapshot.schema.json`).

See [docs/ENGINES.md](docs/ENGINES.md) for detailed comparison and usage guidance.

## Development

Run all tests:
```bash
make test
```

Solve + verify in one step:
```bash
make demo
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for developer setup.

## Architecture

- `src/coords/`: Coordinate system implementations
- `src/pieces/`: Piece definitions and inventory management
- `src/solver/`: Core solving engines and algorithms
- `src/io/`: Input/output handling with schema validation
- `src/reporting/`: Progress tracking and metrics
- `cli/`: Command-line interface
- `tests/`: Test suite
- `docs/`: Documentation

## Development

See `docs/ENGINE_OVERVIEW.md` for architectural details and `docs/devlog.md` for development notes.
