# Engine Overview

This document provides an architectural overview of the ball puzzle solver engines.

## Architecture

The solver uses a modular architecture with pluggable engines, allowing different solving algorithms to be used interchangeably.

### Core Components

#### Engine API (`src/solver/engine_api.py`)
- Abstract base class `SolverEngine` defining the interface
- `SolverResult` dataclass for returning results
- `SolverEngineFactory` for creating engine instances

#### Current Engine (`src/solver/engines/current_engine.py`)
- Stable interface that delegates to the current default engine
- Currently uses DFS engine as the default implementation

#### DFS Engine (`src/solver/engines/dfs_engine.py`)
- Depth-First Search implementation with backtracking
- Supports heuristics, pruning, symmetry breaking, and caching
- Configurable optimization features

### Supporting Systems

#### Heuristics (`src/solver/heuristics.py`)
- Piece ordering strategies
- Placement ordering strategies
- Connectivity and isolation analysis

#### Pruning (`src/solver/pruning.py`)
- Feasibility checks
- Connectivity maintenance
- Unfillable region detection

#### Symmetry Breaking (`src/solver/symbreak.py`)
- Canonical coordinate transformations
- Orientation filtering
- State key generation for caching

#### Transposition Table (`src/solver/tt.py`)
- LRU cache for explored states
- Configurable size limits
- Hash-based state keys

## Coordinate System

The solver uses a Face-Centered Cubic (FCC) lattice coordinate system:

- **Lattice**: `src/coords/lattice_fcc.py`
- **Canonical Form**: `src/coords/canonical.py`

### FCC Lattice Properties
- Each position has up to 12 nearest neighbors
- Supports efficient 3D packing
- Natural for ball puzzle representations

### Canonical Transformations
- Eliminates rotational and translational symmetries
- Reduces search space significantly
- Ensures consistent state representation

## Piece System

### Piece Library (`src/pieces/library_fcc_v1.py`)
- Standard collection of ball puzzle pieces
- Automatic orientation generation
- Canonical piece representations

### Inventory Management (`src/pieces/inventory.py`)
- Tracks available pieces during solving
- Supports backtracking operations
- Maintains placement history

## I/O System

### Schema Validation
- JSON schemas for all data formats
- Container, inventory, solution, and snapshot schemas
- Ensures data integrity and compatibility

### File Formats
- **Containers**: Define puzzle target shapes
- **Inventories**: Define available pieces
- **Solutions**: Store complete puzzle solutions
- **Snapshots**: Save intermediate solver states

## Performance Features

### Optimization Strategies
1. **Heuristic Ordering**: Smart piece and placement selection
2. **Pruning**: Early elimination of impossible branches
3. **Symmetry Breaking**: Avoid exploring equivalent states
4. **Caching**: Transposition table for state memoization

### Metrics and Reporting
- Comprehensive performance metrics collection
- Progress tracking with real-time updates
- Multiple export formats (JSON, HTML, CSV, XML)

## Usage Patterns

### Basic Solving
```python
from solver.engines.current_engine import CurrentEngine

engine = CurrentEngine()
result = engine.solve(container_coords, piece_counts)
```

### Advanced Configuration
```python
from solver.engines.dfs_engine import DFSEngine

engine = DFSEngine(
    use_heuristics=True,
    use_pruning=True,
    use_symmetry_breaking=True,
    use_transposition_table=True
)
```

### Progress Monitoring
```python
from reporting.progress import ProgressTracker

progress = ProgressTracker(use_tqdm=True)
# Engine automatically updates progress during solving
```

## Extension Points

### Adding New Engines
1. Inherit from `SolverEngine`
2. Implement `solve()` and `cancel()` methods
3. Register with `SolverEngineFactory`

### Custom Heuristics
1. Extend `Heuristics` class
2. Override ordering methods
3. Configure engine to use custom heuristics

### Additional Pruning
1. Extend `PruningStrategy` class
2. Add new pruning conditions
3. Integrate with existing pruning pipeline

## Canonical Solution Identity

### Problem Statement
Without deduplication, solver engines can emit multiple solutions that are rotational duplicates of each other under container symmetry. This creates noise in results and wastes computational resources.

### Solution Approach
The solver implements canonical solution identity to ensure each unique solution is emitted only once:

1. **Canonical State Signature**: Each final occupied state is reduced to a canonical form using `canonical_atom_tuple()` from the symmetry utilities
2. **SHA256 Hashing**: The canonical representation is hashed to produce a unique `sid_state_canon_sha256` identifier
3. **Deduplication**: Engines maintain an in-memory set of emitted signatures and skip solutions with duplicate signatures

### Implementation Details
- `src/io/solution_sig.py` provides `canonical_state_signature()` function
- Both `current_engine.py` and `dfs_engine.py` integrate deduplication before solution emission
- Solution JSON includes `sid_state_canon_sha256` field for external verification
- All operations use FCC lattice integer coordinates (no world-space math)

### Benefits
- Eliminates rotated duplicate solutions from output
- Reduces result set size and improves clarity
- Maintains deterministic behavior under container symmetries
- Enables efficient solution comparison and verification

## Performance Considerations

### Memory Usage
- Transposition table size affects memory consumption
- Piece orientations are cached for efficiency
- Progress history can accumulate over long runs
- Solution signature tracking adds minimal memory overhead

### Time Complexity
- Exponential in worst case (NP-complete problem)
- Optimizations provide significant practical speedup
- Timeout mechanisms prevent infinite runs
- Canonical signature computation is O(n log n) where n is occupied cells

### Scalability
- Designed for puzzles up to ~100 pieces
- Performance degrades with larger search spaces
- Consider problem decomposition for very large puzzles
- Signature deduplication scales well with solution count
