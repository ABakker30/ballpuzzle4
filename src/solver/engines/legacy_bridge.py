# Thin bridge for the previous repo's engine.
# Fill `run_legacy_engine` to call the old solver, convert outputs to the normalized format.
from __future__ import annotations
from typing import Dict, Any, Iterator, List, Tuple, Optional

I3 = Tuple[int,int,int]

def run_legacy_engine(container_cells: List[I3],
                      inventory: Dict[str,int],
                      seed: int,
                      max_results: int) -> Iterator[Dict[str, Any]]:
    """
    MUST yield items shaped as ONE of the following (choose A or B):

    A) Direct placements (preferred):
       {"placements": [{"piece":"A","ori":0,"t":[dx,dy,dz]}, ...]}

    B) Covered-cells per placement:
       {"covered_by_piece": [
           {"piece":"A","covered": [[x,y,z], ...]},  # one placement's cells
           ...
       ]}

    All coords must be engine-native FCC ints.
    Yield 0..N solutions (stop at max_results).
    """
    # TODO: IMPLEMENT: call the legacy solver here and convert its output to A or B.
    # For now, this stub yields nothing (no solutions).
    if False:
        yield {}  # pragma: no cover
    return
