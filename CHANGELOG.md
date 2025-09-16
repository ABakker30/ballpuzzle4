# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-16

### Added
- Initial release of Ball Puzzle Solver
- DFS engine with depth-first search optimization
  - Restart mechanisms with pivot cycling
  - MRV (Minimum Remaining Values) heuristics
  - Hole pruning modes (none, single_component, lt4)
  - Time limit enforcement with precise termination
- DLX engine with Algorithm X exact cover solving
  - Dancing Links implementation
  - Bitmap-based state representation
  - Integer coordinate optimization (+14.3% performance)
- Engine-C high-performance solver
  - Bitset-based state management
  - FCC-native operations with 24 integer rotations
  - Disconnected void pruning using flood-fill
  - Deterministic RNG with named substreams
- Modern React UI with 3D visualization
  - Three.js-based solution viewer with interactive controls
  - WebM movie generation with 9:16 aspect ratio
  - Light/dark theme system with automatic OS detection
  - Real-time status monitoring and progress tracking
- Container Standard v1.0
  - Schema-validated JSON format
  - CID (Container ID) verification system
  - FCC coordinate system (i,j,k integers)
  - Designer metadata support
- Comprehensive CLI tooling
  - `cli/solve.py` - Main solver interface
  - `cli/validate_container.py` - Container validation
  - `cli/compute_cid.py` - CID computation and verification
  - `cli/verify.py` - Solution verification
- Complete test suite
  - 41 test modules covering all engines
  - Inventory validation tests
  - Placement generation tests
  - Engine comparison and standardization tests
- Professional documentation
  - Architecture documentation with ADRs
  - Container Standard v1.0 specification
  - API documentation and examples
  - Development guidelines and contributing guide
- GitHub Actions CI/CD
  - Automated testing on Python 3.8, 3.9, 3.10
  - Release automation with tag-based deployment
  - Code coverage reporting
- Legacy results archive
  - 102 historical solution files preserved
  - Multiple container shapes (Shape_2 through Shape_24)
  - Performance benchmarking data

### Performance
- DFS engine: 100+ solutions on 16-cell containers
- DLX engine: 200+ solutions/minute sustained performance
- Engine-C: Optimized for 100+ cell containers
- Time limits: Precise enforcement across all engines
- Memory efficiency: Bitmap operations and integer coordinates

### Technical Details
- FCC lattice coordinate system with 24 proper rotations
- Static piece orientations from verified legacy data
- Canonical deduplication using coordinate signature hashing
- Multi-engine architecture with pluggable solver backends
- Schema validation for all JSON data formats
- Professional error handling and user feedback

[1.0.0]: https://github.com/YourUsername/ballpuzzle4/releases/tag/v1.0.0
