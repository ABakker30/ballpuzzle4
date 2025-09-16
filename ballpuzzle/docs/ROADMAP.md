# Project Roadmap

This roadmap outlines upcoming milestones for the Ball Puzzle project.  
It captures **what to build**, **when**, and **dependencies**.

---

## Phase 1 — Foundations ✅ (done or in progress)
- [x] Status snapshot emission (DFS + DLX engines).
- [x] JSON schema validation for snapshots.
- [x] CLI integration for status output options.
- [x] Web UI polling of `status.json` and KPI display.

---

## Phase 2 — Visualization
- [ ] **View a Solution**
  - Load solution JSON + events JSONL.
  - Timeline scrubber (Play / Pause / Speed).
  - Basic 3D viewer with instanced spheres.
  - Export static image.
- [ ] **Physics (light)**
  - Visual-only: gravity + damping + collisions.
  - Optional "snuggle settle" animation.
- **Dependencies**: Three.js integration, snapshot `stack`.

---

## Phase 3 — Solve Tab Expansion
- [ ] CLI builder (done).
- [ ] Presets for quick runs (DFS quick, DLX demo).
- [ ] Command copy modal.
- [ ] Later: Local runner integration (Start/Stop in UI).
- **Dependencies**: None (runs standalone with CLI copy).

---

## Phase 4 — Puzzle by Hand
- [ ] Interactive play mode.
- [ ] Piece palette with drag-and-drop.
- [ ] Snap-to-FCC lattice.
- [ ] Light physics for realism.
- [ ] Save / load attempts.
- **Dependencies**: Piece library, FCC grid renderer, physics engine.

---

## Phase 5 — Create a Puzzle
- [ ] Load/edit container JSON.
- [ ] Editing tools: add/remove FCC cells, symmetry, rotate, mirror.
- [ ] Inspector (cell count, connectivity, CID).
- [ ] Physics visual aids: grain/rattle test.
- [ ] Export CID + thumbnail.
- **Dependencies**: Lattice editor components, CID calculator.

---

## Phase 6 — Share & UGS Tools
- [ ] Screenshots, clips, and exports.
- [ ] Turntable renders.
- [ ] Solution sharing (export JSON or interactive link).
- **Dependencies**: Viewer, event replay, physics showcase.

---

## Phase 7 — Infrastructure & Packaging
- [ ] PWA support (desktop + mobile installable).
- [ ] Offline cache for last solutions.
- [ ] Optional: Electron/Tauri desktop app (for local runner).
- **Dependencies**: Existing UI, manifest config.

---

## Guiding Principles
- **Incremental**: each phase is self-contained and demoable.
- **Data integrity**: physics never mutates canonical engine data.
- **Cross-platform**: UI works on both desktop and mobile.
- **Schema-first**: new features documented in `docs/` before implementation.

---

## Next Steps
- Finish **Phase 2**: solution viewer with timeline + light physics.
- Gather feedback, then proceed to **Phase 4 (Puzzle by Hand)**.