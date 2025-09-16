# Ideas (Parking Lot)

This file is for collecting ideas, experiments, and "maybe later" features.  
Items here are **not in scope** until they are moved into the official `ROADMAP.md`.  
This helps keep milestones small and focused while preserving future inspiration.

---

## Puzzle & Engine Ideas
- Implement alternative lattices (SC, BCC) with their own piece libraries.
- Try different engine types (GPU backtracking, SAT solver).
- Add heuristic scoring functions for stability-aware placements (bridging, keystone checks).
- Add solution deduplication with canonicalization under container symmetries.

## UI / Visualization Ideas
- Web viewer (PWA) with manual puzzle mode.
- Real-time 3D viewer with drag/drop placement in browser.
- Export solutions to GLTF/OBJ for 3D printing or visualization.
- Animated "snuggle" physics with cannon-es or bullet3.

## Distribution / Platform Ideas
- Publish CLI as PyPI package (`pip install ballpuzzle`).
- Provide Docker image for solver reproducibility.
- Add GitHub Pages docs site from `/docs`.

## Community / Gameplay Ideas
- Leaderboard of manually solved puzzles.
- Weekly small-container puzzle challenges.
- Timed manual solve mode with replay logging.
- Gamified achievements (e.g. "First Pyramid Solve").

---

## Notes
- Keep entries short and clear.
- When ready to prioritize, move an item into the `ROADMAP.md`.
- This list will likely grow faster than milestones are completed — that's expected.
