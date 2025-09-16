# Golden Example Containers

This directory contains curated example containers that demonstrate various features and complexity levels of the Ball Puzzle v1.0 format.

## Container Categories

### Small Containers (4-12 cells)
Perfect for testing and quick validation:
- `tiny_4cell.fcc.json` - Minimal 4-cell container for basic testing
- `simple_8cell.fcc.json` - 8-cell container with simple geometry
- `test_12cell.fcc.json` - 12-cell container for algorithm validation

### Medium Containers (16-40 cells)
Good for development and moderate solving:
- `medium_16cell.fcc.json` - Standard 16-cell container
- `complex_24cell.fcc.json` - 24-cell container with interesting geometry
- `hollow_32cell.fcc.json` - 32-cell hollow structure

### Large Containers (50+ cells)
For performance testing and complex solving:
- `large_64cell.fcc.json` - 64-cell container for performance testing
- `complex_100cell.fcc.json` - 100-cell container with challenging geometry

## Container Features

Each example container includes:
- ✅ Valid v1.0 format with all required fields
- ✅ Verified CID using FCC canonicalization
- ✅ Proper designer metadata
- ✅ Comprehensive documentation
- ✅ Known solving characteristics (solvable/unsolvable, difficulty)

## Usage Examples

```bash
# Validate all examples
python -m cli.validate_container data/containers/examples/ --batch

# Verify all CIDs
python -m cli.compute_cid data/containers/examples/ --batch --verify

# Test solving with different engines
python -m cli.solve data/containers/examples/tiny_4cell.fcc.json --engine dfs --pieces A=4
python -m cli.solve data/containers/examples/medium_16cell.fcc.json --engine dlx --time-limit 30
```

## Container Specifications

| Container | Cells | Geometry | Solvable | Difficulty | Purpose |
|-----------|-------|----------|----------|------------|---------|
| tiny_4cell | 4 | Linear | Yes | Trivial | Basic testing |
| simple_8cell | 8 | Cubic | Yes | Easy | Algorithm validation |
| test_12cell | 12 | L-shape | Yes | Easy | Edge case testing |
| medium_16cell | 16 | Pyramid | Yes | Medium | Standard benchmark |
| complex_24cell | 24 | Spiral | Yes | Hard | Complex geometry |
| hollow_32cell | 32 | Hollow cube | No | N/A | Unsolvable test |
| large_64cell | 64 | Fractal | Yes | Very Hard | Performance test |
| complex_100cell | 100 | Organic | Yes | Extreme | Stress test |

## Design Guidelines

When creating new example containers:
1. Use meaningful, descriptive names
2. Include complete designer metadata
3. Verify CID computation matches stored value
4. Document solving characteristics
5. Test with multiple engines
6. Validate against v1.0 schema

## Testing Integration

These containers are used in:
- Automated test suites
- Engine performance benchmarks
- CID computation validation
- Schema compliance testing
- UI integration testing
