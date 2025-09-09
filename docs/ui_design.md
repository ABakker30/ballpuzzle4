# UI Design Specification

## Overview
The Ball Puzzle UI supports four main user functions:

1. **Solve a Puzzle** – Run a solver engine on a container.
2. **Create a Puzzle** – Build or edit puzzle containers.
3. **View a Solution** – Load and explore solved states.
4. **Puzzle by Hand** – Interactively attempt puzzles.

The app is designed for both **desktop and mobile**, with PWA support for installability.

---

## Solve a Puzzle
- **Primary action**: select container + press "Solve".
- Shows a **CLI string** in a modal for now (copyable to run locally).
- Presets for quick DFS or DLX runs.
- **Advanced options**: time, node, solution limits, `k`, interval, stack cap, phase.
- Later: integration with local runner for **Start/Stop** directly in the UI.

---

## Create a Puzzle
- **Start from scratch**, or **load/edit existing container**.
- Editing tools:
  - Add/remove FCC lattice cells.
  - Symmetry fill, mirror, rotate, translate.
- **Inspector**:
  - Cell count, connectivity, bounds.
  - CID hash for container.
- **Physics (visual aid)**:
  - Grain test: drop spheres to check concavity.
  - Rattle test: subtle jiggle to reveal tight spots.
- **Export**: JSON, CID, thumbnail.

---

## View a Solution
- Load **container + solution + events.jsonl**.
- **Controls**:
  - Timeline scrubber.
  - Play / Pause / Speed.
- **UGS / Share tools**:
  - Screenshots, short clips, turntable, watermark.
  - Export JSON.
- **Physics (visual only)**:
  - Off: static render.
  - Light: gentle gravity + damping.
  - Showcase: snuggle settle at start/end.
- Physics is **non-destructive** and purely visual.

---

## Puzzle by Hand
- **Interactive play** mode.
- **Piece palette**: select, drag, drop into container.
- **Snap-to-FCC**: pieces align automatically.
- **Helpers**: hints, ghost previews, valid/invalid feedback.
- **Light physics**:
  - Gentle gravity + collisions.
  - Snap tolerance.
  - Snuggle settle after placement.
- **Controls**: undo/redo, reset, save attempt.

---

## Physics Levels (Shared)
- **Off**: no physics.
- **Light**: gravity + damping + collisions, enforced snap.
- **Showcase**: light + short settle animations.
- **Deterministic**: fixed seed for repeatable exports.

---

## Navigation
- **Tabs**: Solve | Create | View | Puzzle | Status.
- **Desktop**: sidebar tabs.
- **Mobile**: bottom tabs.
- **Status tab**: live KPIs (engine, elapsed, nodes, pruned, depth, solutions).

---

## Milestones
1. **Status + Solve (CLI string builder)** – current baseline.
2. **View**: loader + timeline UI + share toolbelt (no physics).
3. **View**: add physics toggles.
4. **Puzzle by Hand**: interactive with light physics.
5. **Create**: editor with symmetry, validation, physics tests.

---

## Data Rules
- Viewer **never mutates engine data**.
- Physics is **visual only**.
- Create/Edit containers must **validate before save** and compute CID.
