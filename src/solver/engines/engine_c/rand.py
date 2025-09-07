"""Deterministic RNG with named substreams for reproducible solving."""

import hashlib
from typing import List


class Rng:
    """Deterministic random number generator with substream support."""
    
    def __init__(self, seed: int):
        """Initialize RNG with integer seed."""
        self.seed = seed
        self.state = seed
    
    def split(self, tag: str) -> 'Rng':
        """Create a new RNG for a named substream."""
        # Hash the tag with current seed to create deterministic subseed
        hash_input = f"{self.seed}:{tag}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).digest()
        subseed = int.from_bytes(hash_digest[:4], byteorder='big')
        return Rng(subseed)
    
    def randint(self, a: int, b: int) -> int:
        """Generate random integer in range [a, b] inclusive."""
        if a > b:
            raise ValueError("a must be <= b")
        
        # Simple linear congruential generator
        self.state = (self.state * 1103515245 + 12345) & 0x7fffffff
        range_size = b - a + 1
        return a + (self.state % range_size)
    
    def shuffle(self, items: List) -> List:
        """Shuffle list in-place and return it."""
        # Fisher-Yates shuffle
        for i in range(len(items) - 1, 0, -1):
            j = self.randint(0, i)
            items[i], items[j] = items[j], items[i]
        return items
