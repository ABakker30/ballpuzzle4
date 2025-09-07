"""Random number generator utilities for puzzle solving."""

import random
from typing import List, TypeVar, Optional

T = TypeVar('T')


class RandomNumberGenerator:
    """Seeded random number generator for reproducible puzzle solving."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize RNG with optional seed.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        self.rng = random.Random(seed)
    
    def shuffle(self, items: List[T]) -> List[T]:
        """Shuffle a list in-place and return it.
        
        Args:
            items: List to shuffle
            
        Returns:
            Shuffled list (same object)
        """
        self.rng.shuffle(items)
        return items
    
    def choice(self, items: List[T]) -> T:
        """Choose a random item from a list.
        
        Args:
            items: List to choose from
            
        Returns:
            Random item from the list
            
        Raises:
            IndexError: If list is empty
        """
        return self.rng.choice(items)
    
    def sample(self, items: List[T], k: int) -> List[T]:
        """Sample k items from a list without replacement.
        
        Args:
            items: List to sample from
            k: Number of items to sample
            
        Returns:
            List of sampled items
        """
        return self.rng.sample(items, k)
    
    def random(self) -> float:
        """Generate random float between 0 and 1.
        
        Returns:
            Random float in [0, 1)
        """
        return self.rng.random()
    
    def randint(self, a: int, b: int) -> int:
        """Generate random integer between a and b inclusive.
        
        Args:
            a: Lower bound (inclusive)
            b: Upper bound (inclusive)
            
        Returns:
            Random integer in [a, b]
        """
        return self.rng.randint(a, b)
    
    def reseed(self, seed: Optional[int] = None):
        """Reseed the random number generator.
        
        Args:
            seed: New seed value
        """
        self.seed = seed
        self.rng = random.Random(seed)
