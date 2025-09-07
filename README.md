# Ball Puzzle Solver

A modern ball puzzle solver with clean architecture and multiple solving engines.

## Overview

This project implements a ball puzzle solver using a face-centered cubic (FCC) lattice coordinate system. It features a modular architecture with pluggable solving engines, comprehensive piece libraries, and robust I/O handling.

## Features

- **Multiple Coordinate Systems**: FCC lattice with canonical transformations
- **Piece Library**: Comprehensive FCC piece definitions
- **Solving Engines**: Multiple algorithms including DFS
- **Heuristics & Pruning**: Advanced optimization techniques
- **Symmetry Breaking**: Efficient search space reduction
- **Schema Validation**: JSON schema validation for all data formats
- **Progress Reporting**: Real-time solving progress and metrics
- **CLI Interface**: Command-line solving interface

## Installation

```bash
pip install -e .
```

## Usage

### Solving Puzzles

```bash
python -m cli.solve containers/tiny_4.fcc.json --engine dlx --pieces A=1,B=1
```

### Verifying Solutions

Validate that a solution file is correct and complete:

```bash
python -m cli.verify solution.json container.json
```

Returns exit code 0 for valid solutions, 2 for invalid ones. See [docs/VERIFY.md](docs/VERIFY.md) for detailed usage and examples.

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
