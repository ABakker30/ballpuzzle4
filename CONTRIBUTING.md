# Contributing to Ball Puzzle Solver

Thank you for your interest in contributing to the Ball Puzzle Solver project!

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+ (for UI development)
- Git

### Local Development
```bash
# Clone the repository
git clone https://github.com/YourUsername/ballpuzzle4.git
cd ballpuzzle4

# Set up Python environment
cd ballpuzzle
pip install -r requirements.txt

# Set up UI development (optional)
cd ui
npm install
```

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes
```bash
# Run Python tests
cd ballpuzzle
python -m pytest tests/ -v

# Test specific engines
python -m pytest tests/test_dfs_with_real_placements.py -v
python -m pytest tests/test_inventory_respected.py -v

# Test UI (if applicable)
cd ui
npm test
```

### 4. Commit Changes
Use conventional commit format:
```bash
git commit -m "feat: add new solver optimization"
git commit -m "fix: resolve DFS duplicate inventory issue"
git commit -m "docs: update API documentation"
```

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
# Create Pull Request on GitHub
```

## Code Style Guidelines

### Python
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings for public functions
- Keep functions focused and testable

### TypeScript/React
- Use TypeScript for all new code
- Follow React best practices
- Use functional components with hooks
- Maintain consistent naming conventions

## Testing Requirements

### Required Tests
- Unit tests for new functions/classes
- Integration tests for engine changes
- UI component tests for React changes
- End-to-end tests for CLI modifications

### Test Categories
- `tests/test_*_basic.py` - Basic functionality tests
- `tests/test_*_with_real_placements.py` - Integration tests
- `tests/test_inventory_*.py` - Inventory validation tests
- `tests/test_engine_*.py` - Engine-specific tests

## Engine Development

### Adding New Engines
1. Implement `EngineProtocol` interface
2. Add to `src/solver/registry.py`
3. Create comprehensive test suite
4. Update CLI to support new engine
5. Add documentation and examples

### Engine Requirements
- Must emit `solution` and `done` events
- Must compute `sid_state_canon_sha256` for deduplication
- Must handle time limits gracefully
- Must validate input containers and inventories

## UI Development

### Component Structure
- Keep components focused and reusable
- Use TypeScript interfaces for props
- Follow existing styling patterns
- Test with different container sizes

### 3D Visualization
- Use Three.js best practices
- Optimize for performance
- Support both light and dark themes
- Ensure responsive design

## Documentation

### Required Documentation
- Update README.md for new features
- Add entries to CHANGELOG.md
- Update API documentation
- Include usage examples

### Documentation Style
- Clear, concise explanations
- Code examples with expected output
- Performance characteristics where relevant
- Cross-references to related functionality

## Release Process

### Version Numbering
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, performance improvements

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped appropriately
- [ ] Tag created with release notes

## Getting Help

- Open an issue for bugs or feature requests
- Use discussions for questions and ideas
- Check existing issues before creating new ones
- Provide detailed information for bug reports

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

Thank you for contributing to Ball Puzzle Solver!
