# Containers

- **samples/** — curated examples used in docs and quick demos
- **legacy_fixed/** — auto-converted legacy containers normalized to the current schema:
  ```json
  { "name": "...", "lattice_type": "fcc", "coordinates": [[x,y,z], ...] }
  ```

## Notes

- All coordinates are engine-native FCC integers (rhombohedral)
- Extra legacy fields removed; schema is minimal to match container.schema.json
- Most containers have 100 cells each, suitable for medium-scale solving tests
- Mirror variants (*.mirror.json) provide additional geometric diversity

## Usage

Solve any container with the CLI:
```bash
python -m cli.solve data/containers/legacy_fixed/Shape_1.json --engine dfs --pieces A=25
```

Verify solutions:
```bash
python -m cli.verify solution.json data/containers/legacy_fixed/Shape_1.json
```
