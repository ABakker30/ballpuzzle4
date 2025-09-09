# Architecture Overview

## High-Level Structure
The Ball Puzzle project is split into two major parts:

1. **Engines (DFS, DLX, C)**
   - Responsible for searching puzzle solutions.
   - Emit event logs (JSONL) and status snapshots (JSON).
   - Pure computational core, no rendering logic.

2. **UI (Web, React + Vite + TypeScript + Three.js)**
   - Reads container, solution, and status files.
   - Provides tabs for user functions: Solve, Create, View, Puzzle, Status.
   - Visualizes puzzles and solutions with optional physics.

---

## Engines
- **DFS Engine**  
  Depth-first search with pruning. Produces detailed event logs and stack-based status snapshots.

- **DLX Engine**  
  Exact cover solver with matrix operations. Also emits periodic status snapshots.

- **C Engine (future)**  
  Optimized C implementation for high performance.

**Common Traits:**
- Emit `status.json` on a timer for monitoring.
- Emit `events.jsonl` for replay and debugging.
- Pure integer FCC lattice representation (piece index, orient index, lattice coordinates).

---

## UI
- **Framework**: React + Vite + TypeScript.
- **State**: Zustand for app-wide state.
- **3D**: Three.js for rendering lattice containers, pieces, and solutions.
- **Tabs**:
  - Solve → build CLI string and monitor status.
  - Create → container editor with symmetry/validation.
  - View → load solutions, timeline, share tools.
  - Puzzle → hand play with light physics.
  - Status → engine KPIs.
- **Physics**: light, visual-only, optional.

---

## Data Flow
1. **Input**: Container JSON + optional Solution JSON.
2. **Engine**: Runs solve → emits `status.json` + `events.jsonl`.
3. **UI**: Polls `status.json` (Plan A), renders KPIs + stack geometry.
4. **Optional**: Replay events for timeline or shareable exports.

---

## Design Principles
- **Separation of concerns**: engines compute, UI visualizes.
- **Determinism**: integer FCC lattice → reproducible results.
- **Visual physics**: never alters canonical engine data.
- **Extensibility**: CLI options and schema versions support future features.

---

## Future Extensions
- Local runner daemon or desktop app for full Start/Stop integration.
- Puzzle sharing / online galleries.
- Expanded physics modes (interactive puzzles, showcase animations).
- Modular export tools (video, image, solution registries).
