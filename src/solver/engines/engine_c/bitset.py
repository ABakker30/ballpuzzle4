"""Integer-backed bitset operations for efficient state representation."""

from typing import List


def popcount(x: int) -> int:
    """Count number of set bits in integer."""
    return bin(x).count('1')


def bitset_from_indices(indices: List[int], max_bits: int) -> int:
    """Create bitset from list of bit indices."""
    result = 0
    for i in indices:
        if 0 <= i < max_bits:
            result |= (1 << i)
    return result


def bitset_to_indices(bitset: int) -> List[int]:
    """Convert bitset to list of set bit indices."""
    indices = []
    bit = 0
    while bitset:
        if bitset & 1:
            indices.append(bit)
        bitset >>= 1
        bit += 1
    return indices


def bitset_intersects(a: int, b: int) -> bool:
    """Check if two bitsets have any common set bits."""
    return (a & b) != 0


def bitset_union(a: int, b: int) -> int:
    """Union of two bitsets."""
    return a | b


def bitset_intersection(a: int, b: int) -> int:
    """Intersection of two bitsets."""
    return a & b


def bitset_difference(a: int, b: int) -> int:
    """Difference of two bitsets (a - b)."""
    return a & (~b)


def bitset_complement(bitset: int, num_bits: int) -> int:
    """Complement of bitset within num_bits."""
    mask = (1 << num_bits) - 1
    return (~bitset) & mask


def all_bits_mask(num_bits: int) -> int:
    """Create mask with all num_bits set."""
    return (1 << num_bits) - 1
