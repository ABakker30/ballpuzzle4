from typing import List, TypeVar, Optional
import random

T = TypeVar("T")

def tie_shuffle(items: List[T], seed: Optional[int]) -> List[T]:
    """Deterministic shuffle if seed is not None; otherwise identity."""
    if seed is None: 
        return list(items)  # Return a copy, not the original
    rnd = random.Random(seed)
    items2 = list(items)
    rnd.shuffle(items2)
    return items2
