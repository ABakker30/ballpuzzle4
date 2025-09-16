#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys, shutil
from pathlib import Path
from typing import Dict, Any, Tuple, List, Set, Optional

I3 = Tuple[int,int,int]

def _read_json(p: Path) -> Dict[str,Any]:
    return json.loads(p.read_text(encoding="utf-8"))

def _write_json(p: Path, obj: Dict[str,Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

def main():
    try:
        from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
        from src.io.solution_sig import canonical_state_signature
        from src.io.schema import load_schema
        from jsonschema import validate
        from src.io.container import load_container
        from src.solver.symbreak import container_symmetry_group
    except Exception as e:
        print("[ERROR] Run from repo root with project on PYTHONPATH. Details:", e, file=sys.stderr)
        sys.exit(2)

    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Directory with legacy solution JSON files")
    ap.add_argument("--out", help="Output directory (default: IN-PLACE if --inplace)")
    ap.add_argument("--inplace", action="store_true", help="Convert files in place (writes .bak once)")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--pattern", default="*.json")
    ap.add_argument("--containers-root", help="Root of normalized containers for computing containerCid")
    ap.add_argument("--validate", action="store_true", help="Validate outputs against solution schema")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src_root = Path(args.src).resolve()
    if not args.out and not args.inplace:
        print("[ERROR] specify --out or --inplace", file=sys.stderr); sys.exit(2)
    out_root = Path(args.out).resolve() if args.out else None
    cont_root = Path(args.containers_root).resolve() if args.containers_root else None

    files = list(src_root.rglob(args.pattern)) if args.recursive else list(src_root.glob(args.pattern))
    if not files:
        print("[INFO] no files matched."); return

    schema = load_schema("solution.schema.json") if args.validate else None
    lib = load_fcc_A_to_Y()

    def infer_pose_from_cells(pid: str, covered_cells: List[I3]) -> Optional[Dict[str,Any]]:
        pdef = lib.get(pid)
        if not pdef: return None
        cov = tuple(sorted(tuple(map(int,c)) for c in covered_cells))
        cov_set = set(cov)
        best: Optional[Tuple[int,Tuple[int,int,int]]] = None
        for oi, orient in enumerate(pdef.orientations):
            for anchor in cov:
                dx = anchor[0] - orient[0][0]
                dy = anchor[1] - orient[0][1]
                dz = anchor[2] - orient[0][2]
                placed = {(u[0]+dx,u[1]+dy,u[2]+dz) for u in orient}
                if placed == cov_set:
                    key = (oi,(dx,dy,dz))
                    if best is None or key < best:
                        best = key
        if best is None: return None
        oi,(dx,dy,dz) = best
        return {"piece": pid, "ori": oi, "t": [dx,dy,dz]}

    def pieces_used(placements: List[Dict[str,Any]]) -> Dict[str,int]:
        counts: Dict[str,int] = {}
        for pl in placements:
            counts[pl["piece"]] = counts.get(pl["piece"], 0) + 1
        return counts

    def find_container_path(legacy_obj: Dict[str,Any]) -> Optional[Path]:
        if not cont_root: return None
        name = legacy_obj.get("container_name")
        if name:
            p = cont_root / f"{name}.json"
            if p.exists(): return p
        legacy_path = legacy_obj.get("container_path")
        if legacy_path:
            base = Path(legacy_path).name
            p = cont_root / base
            if p.exists(): return p
        return None

    print(f"[INFO] found {len(files)} legacy solution(s)")
    for f in files:
        try:
            if args.dry_run:
                print(f"[DRY] {f}"); continue

            if args.inplace:
                bak = f.with_suffix(f.suffix + ".bak")
                if not bak.exists():
                    shutil.copy2(f, bak)
                dst = f
            else:
                rel = f.relative_to(src_root)
                dst = out_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)

            legacy = _read_json(f)
            if "pieces" not in legacy:
                print(f"[FAIL] {f}: missing 'pieces' array", file=sys.stderr); continue

            placements: List[Dict[str,Any]] = []
            used_cells: Set[I3] = set()
            for p in legacy["pieces"]:
                pid = str(p.get("id","")).strip()
                cells_ijk = p.get("cells_ijk") or []
                if not pid or len(cells_ijk) == 0:
                    print(f"[FAIL] {f}: invalid piece {p!r}", file=sys.stderr); placements=[]; break
                pose = infer_pose_from_cells(pid, [tuple(c) for c in cells_ijk])
                if pose is None:
                    print(f"[FAIL] {f}: cannot infer (ori,t) for piece {pid}", file=sys.stderr); placements=[]; break
                placements.append(pose)
                pdef = lib[pid]
                ori = pdef.orientations[pose["ori"]]
                dx,dy,dz = pose["t"]
                for u in ori:
                    used_cells.add((u[0]+dx,u[1]+dy,u[2]+dz))
            if not placements:
                continue

            container_cid = ""
            cpath = find_container_path(legacy)
            if cpath and cpath.exists():
                cont = load_container(str(cpath))
                container_cid = cont.get("cid_sha256","")

            new_sol = {
                "version": 1,
                "lattice": "fcc",
                "containerCidSha256": container_cid,
                "piecesUsed": pieces_used(placements),
                "placements": placements,
                "sid_state_sha256": "legacy_import",
                "sid_route_sha256": "legacy_import",
                "sid_state_canon_sha256": sid_state_canonical_sha256(list(used_cells))
            }

            if schema:
                validate(instance=new_sol, schema=schema)

            _write_json(dst, new_sol)
            print(f"[OK] {f} -> {dst}")

        except Exception as e:
            print(f"[ERROR] {f}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
