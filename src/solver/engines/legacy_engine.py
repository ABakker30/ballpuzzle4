from __future__ import annotations
from typing import Iterator, Dict, List, Tuple, Set, Any
import time
from ..engine_api import EngineProtocol, EngineOptions, SolveEvent
from ...pieces.library_fcc_v1 import load_fcc_A_to_Y
from ...solver.symbreak import container_symmetry_group
from ...io.solution_sig import canonical_state_signature
from .legacy_bridge import run_legacy_engine

I3 = Tuple[int,int,int]

class LegacyEngine(EngineProtocol):
    name = "legacy"

    def solve(self, container, inventory, pieces, options: EngineOptions) -> Iterator[SolveEvent]:
        """
        Adapter: calls the bridge to get legacy results, converts to normalized placements,
        computes canonical SID, and emits solution/done events.
        """
        t0 = time.time()
        seed = int(options.get("seed", 0))
        max_results = int(options.get("max_results", 1))

        # Engine-native cells
        cells_sorted: List[I3] = sorted(tuple(map(int,c)) for c in container["coordinates"])
        container_set = set(cells_sorted)
        symGroup = container_symmetry_group(cells_sorted)
        smallMode = (len(cells_sorted) <= 32)

        # Load A–Y library to reconstruct placements if legacy returns covered sets
        lib = load_fcc_A_to_Y()

        def infer_pose_from_covered(pid: str, covered: List[I3]) -> Dict[str, Any] | None:
            """
            Given a piece id and the exact cells that piece covers, infer (ori, t).
            Try all orientations; if any translate to the covered set, return that pose.
            """
            pdef = lib.get(pid)
            if not pdef:
                return None
            cov_set = set(tuple(map(int,c)) for c in covered)
            for oi, orient in enumerate(pdef.orientations):
                # try matching first atom of orientation to each covered cell
                for anchor_cov in cov_set:
                    dx = anchor_cov[0] - orient[0][0]
                    dy = anchor_cov[1] - orient[0][1]
                    dz = anchor_cov[2] - orient[0][2]
                    placed = {(u[0]+dx,u[1]+dy,u[2]+dz) for u in orient}
                    if placed == cov_set:
                        return {"piece": pid, "ori": oi, "t": [dx,dy,dz]}
            return None

        results = 0

        # call the legacy engine via bridge
        for raw in run_legacy_engine(cells_sorted, inventory.get("pieces", {}) or {}, seed, max_results):
            # Normalize into `placements`
            placements: List[Dict[str,Any]] = []

            if "placements" in raw:
                # Direct normalized placements path
                placements = list(raw["placements"])

            elif "covered_by_piece" in raw:
                # Reconstruct (piece, ori, t) for each placement
                for item in raw["covered_by_piece"]:
                    pid = item["piece"]; cov = [tuple(map(int,c)) for c in item["covered"]]
                    pose = infer_pose_from_covered(pid, cov)
                    if pose is None:
                        # invalid or ambiguous covered set
                        continue
                    placements.append(pose)

            else:
                # Unknown legacy result shape; skip
                continue

            # Compute canonical SID from union of covered cells
            used_cells: Set[I3] = set()
            for pl in placements:
                pid, oi, (dx,dy,dz) = pl["piece"], int(pl["ori"]), tuple(pl["t"])
                pdef = lib.get(pid)
                if not pdef: continue
                orient = pdef.orientations[oi]
                for u in orient:
                    c = (u[0]+dx,u[1]+dy,u[2]+dz)
                    if c not in container_set:
                        # out-of-bounds: reject solution
                        used_cells.clear(); break
                    used_cells.add(c)
                if not used_cells:
                    break
            if not used_cells:
                continue  # bad solution

            sid_canon = canonical_state_signature(used_cells, symGroup)
            sol = {
                "containerCidSha256": container.get("cid_sha256", ""),
                "lattice": "fcc",
                "piecesUsed": inventory.get("pieces", {}),
                "placements": placements,
                "sid_state_sha256": "legacy_state",
                "sid_route_sha256": "legacy_route",
                "sid_state_canon_sha256": sid_canon,
            }
            yield {"t_ms": int((time.time()-t0)*1000), "type":"solution", "solution": sol}
            results += 1
            if results >= max_results:
                break

        # done event
        yield {"t_ms": int((time.time()-t0)*1000), "type":"done",
               "metrics": {"solutions": results, "nodes": 0, "pruned": 0,
                           "bestDepth": 0, "smallMode": smallMode,
                           "symGroup": len(symGroup), "seed": seed}}
