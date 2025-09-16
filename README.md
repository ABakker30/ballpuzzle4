# Ball Puzzle Solver

A comprehensive FCC (Face-Centered Cubic) lattice ball puzzle solver with multiple engines, 3D visualization, and modern tooling.

## Features

### 🚀 Multiple Solver Engines
- **DFS Engine** - Depth-first search with optimizations (restarts, MRV heuristics, hole pruning)
- **DLX Engine** - Algorithm X exact cover solving with Dancing Links
- **Engine-C** - High-performance bitset-based solver for large containers

### 🎨 Modern UI
- **3D Visualization** - Interactive Three.js-based solution viewer
- **Movie Generation** - Export WebM videos of solution animations
- **Theme Support** - Light/dark themes with automatic OS detection
- **Real-time Monitoring** - Live status updates during solving

### 🛠️ Professional Tooling
- **CLI Interface** - Complete command-line tools for solving and validation
- **Container Standard v1.0** - Schema-validated container format with CID verification
- **Comprehensive Testing** - 41 test modules with full engine coverage
- **GitHub Actions** - Automated testing and release workflows

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for UI)

### Installation
```bash
git clone https://github.com/YourUsername/ballpuzzle4.git
cd ballpuzzle4/ballpuzzle
pip install -r requirements.txt
```

### Basic Usage
```bash
# Solve with DFS engine
python -m cli.solve "data/containers/legacy_fixed/16 cell container.json" --engine dfs --time-limit 30

# Solve with DLX engine  
python -m cli.solve "data/containers/legacy_fixed/16 cell container.json" --engine dlx --max-results 10

# Launch UI
cd ui
npm install
npm run dev
```

## Architecture

### Core Components
- `src/solver/engines/` - Solver engine implementations
- `src/coords/` - FCC lattice coordinate system utilities
- `src/pieces/` - Piece library and inventory management
- `src/io/` - Schema-validated I/O for containers and solutions
- `cli/` - Command-line interface tools
- `ui/` - React-based 3D visualization interface

### Container Standard v1.0
All containers use a standardized JSON format with:
- FCC coordinate system (i,j,k integers)
- CID (Container ID) for verification
- Schema validation for data integrity
- Designer metadata support

## Performance

### Benchmark Results
- **16-cell containers**: 100+ solutions in seconds
- **40-cell containers**: 292+ solutions in 2 minutes  
- **100-cell containers**: Optimized for large-scale problems
- **Time limits**: Precise enforcement with graceful termination

### Engine Comparison
| Engine | Best For | Performance | Features |
|--------|----------|-------------|----------|
| DFS | Medium containers (4-20 pieces) | Fast startup | Restarts, heuristics |
| DLX | Exact cover problems | Consistent | Mathematical rigor |
| Engine-C | Large containers (20+ pieces) | Highest throughput | Bitset operations |

## Development

### Running Tests
```bash
cd ballpuzzle
python -m pytest tests/ -v
```

### Contributing
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Release Process
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Tag releases: `git tag -a v1.1.0 -m "Release v1.1.0"`
- GitHub Actions automatically creates releases from tags

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FCC lattice mathematics and coordinate systems
- Algorithm X and Dancing Links implementation
- Three.js for 3D visualization
- React ecosystem for modern UI development

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
