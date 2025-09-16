# ADR-0001: Engine Lattice-Only Architecture

## Status
Accepted

## Context
The ball puzzle solver needs to handle 3D spatial arrangements of spherical pieces within containers. We need to decide on the coordinate system and spatial representation that will be used throughout the solver.

## Decision
We will use a Face-Centered Cubic (FCC) lattice-only architecture for all spatial representations in the solver.

## Rationale

### FCC Lattice Benefits
1. **Natural Ball Packing**: FCC is the optimal packing arrangement for spheres in 3D space
2. **Connectivity**: Each position has 12 nearest neighbors vs 6 in cubic lattice
3. **Efficiency**: Reduces the search space compared to continuous coordinates
4. **Symmetry**: Well-defined rotational symmetries for optimization

### Alternative Approaches Considered
1. **Continuous Coordinates**: Too complex, infinite search space
2. **Cubic Lattice**: Suboptimal packing, fewer neighbor connections
3. **Hexagonal Close Packing**: Similar to FCC but more complex implementation
4. **Mixed Approach**: Would complicate the architecture unnecessarily

### Implementation Implications
- All pieces are defined in FCC coordinates
- All containers are defined in FCC coordinates
- Solver algorithms work exclusively with discrete lattice positions
- Coordinate transformations handle rotations and translations within the lattice

## Consequences

### Positive
- Simplified spatial reasoning
- Efficient neighbor calculations
- Natural symmetry operations
- Reduced search space
- Consistent coordinate system throughout

### Negative
- Limited to lattice-aligned arrangements
- Cannot represent arbitrary orientations
- May not match physical puzzle constraints exactly
- Requires FCC-specific algorithms

### Neutral
- Need to implement FCC-specific coordinate operations
- All input data must be converted to FCC representation
- Visualization tools must understand FCC coordinates

## Implementation Notes
- `FCCLattice` class handles coordinate operations
- `CanonicalCoordinate` provides symmetry operations
- All piece definitions use FCC coordinates
- Container definitions use FCC coordinates
- Solver engines work with FCC coordinate sets

## Related Decisions
- Coordinate system choice affects piece library design
- Symmetry breaking strategies depend on FCC properties
- Visualization and I/O must handle FCC coordinates

## Review Date
This decision should be reviewed if:
- Performance issues arise from lattice limitations
- New puzzle types require non-lattice arrangements
- Alternative coordinate systems show significant advantages
