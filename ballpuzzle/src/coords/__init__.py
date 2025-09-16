"""Coordinate system implementations for ball puzzle solving.

This module provides coordinate system abstractions for representing
positions in 3D space, with a focus on face-centered cubic (FCC) lattices.
"""

from .canonical import CanonicalCoordinate
from .lattice_fcc import FCCLattice

__all__ = ["CanonicalCoordinate", "FCCLattice"]
