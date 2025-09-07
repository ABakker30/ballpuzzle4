# Solution Verifier CLI

The `verify-solution` command validates a `solution.json` against its `container.json`.  
It ensures that:

- All placements expand correctly using the official A–Y piece library.
- No covered cell lies outside the container.
- No two pieces overlap.
- The union of all covered cells exactly equals the container cells.
- The stored canonical SID (`sid_state_canon_sha256`) matches a recomputed one.

---

## Usage

```bash
python -m cli.verify solution.json container.json
```

### Arguments
- `solution.json` — a file produced by the solver (DFS or DLX engines).
- `container.json` — the original container definition file.

### Exit Codes
- `0` — Solution is valid.
- `2` — Solution is invalid (coverage, overlap, out-of-bounds, or SID mismatch).
- `1` — Usage error (wrong arguments).

## Example: Valid Solution
```bash
python -m cli.verify out/solution.json data/containers/tiny_4.fcc.json
```

Output:
```
solution verified ok
```

Exit code: 0

## Example: Overlap Detected
```bash
python -m cli.verify bad_overlap.json data/containers/tiny_4.fcc.json
```

Output:
```
overlap at (0, 0, 0)
```

Exit code: 2

## Example: Missing Cells
```bash
python -m cli.verify bad_missing.json data/containers/tiny_4.fcc.json
```

Output:
```
missing cells: [(1, 0, 0)]
```

Exit code: 2

## Example: SID Mismatch
```bash
python -m cli.verify tampered_sid.json data/containers/tiny_4.fcc.json
```

Output:
```
canonical sid mismatch
stored: d41d8cd98f00b204e9800998ecf8427e
recomputed: 5e884898da28047151d0e56f8dc62927
```

Exit code: 2

## Notes
- The verifier relies on the engine's FCC piece library (A–Y).
- It does not attempt to re-solve; it simply reconstructs coverage from placements.
- Use it in CI/CD pipelines to ensure only valid, canonical solutions are published.

---

✅ drop this as `docs/VERIFY.md`, commit alongside m15, and your repo now has user-facing verification documentation.
