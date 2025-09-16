# Contributing

## Dev Setup

1. Python 3.10+
2. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```

3. Install deps:
   ```bash
   pip install -r requirements.txt
   ```

## Running Tests

```bash
python -m pytest -q
```

## Common Commands

Solve a container:
```bash
python -m cli.solve tests/data/containers/tiny_4.fcc.json --engine dfs --pieces A=1
```

Verify a solution:
```bash
python -m cli.verify solution.json container.json
```

## Code Style

- Python 3.10 typing
- Use black and ruff for formatting/linting.
