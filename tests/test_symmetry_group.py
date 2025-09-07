import unittest
from src.coords.symmetry_fcc import all_fcc_rotations, canonical_atom_tuple, apply_rot
from src.solver.symbreak import container_symmetry_group

class TestSymmetryGroup(unittest.TestCase):
    
    def test_fcc_rotations_count(self):
        """Test that we get exactly 24 FCC rotations."""
        rotations = all_fcc_rotations()
        self.assertEqual(len(rotations), 24)
    
    def test_rotation_determinant(self):
        """Test that all rotations have determinant +1."""
        rotations = all_fcc_rotations()
        for R in rotations:
            det = (R[0][0] * (R[1][1] * R[2][2] - R[1][2] * R[2][1]) -
                   R[0][1] * (R[1][0] * R[2][2] - R[1][2] * R[2][0]) +
                   R[0][2] * (R[1][0] * R[2][1] - R[1][1] * R[2][0]))
            self.assertEqual(det, 1)
    
    def test_canonical_atom_tuple(self):
        """Test canonical atom tuple calculation."""
        # Test that canonical form is deterministic
        atoms = ((0,0,0), (1,0,0))
        canon1 = canonical_atom_tuple(atoms)
        canon2 = canonical_atom_tuple(atoms)
        self.assertEqual(canon1, canon2)
        
        # Test rotation equivalence - different orientations should give same canonical form
        atoms1 = ((0,0,0), (1,0,0))
        atoms2 = ((0,0,0), (0,1,0))  # 90-degree rotation
        canon1 = canonical_atom_tuple(atoms1)
        canon2 = canonical_atom_tuple(atoms2)
        self.assertEqual(canon1, canon2)
        
        # Test that canonical form is sorted
        atoms = ((1,0,0), (0,0,0))  # unsorted input
        canon = canonical_atom_tuple(atoms)
        self.assertEqual(canon, tuple(sorted(canon)))
    
    def test_apply_rotation(self):
        """Test rotation application."""
        # Identity rotation
        identity = ((1,0,0), (0,1,0), (0,0,1))
        point = (1, 2, 3)
        result = apply_rot(identity, point)
        self.assertEqual(result, point)
        
        # 90-degree rotation around z-axis
        rot_z = ((0,1,0), (-1,0,0), (0,0,1))
        point = (1, 0, 0)
        result = apply_rot(rot_z, point)
        self.assertEqual(result, (0, -1, 0))
    
    def test_container_symmetry_group_cube(self):
        """Test symmetry group for a cube container."""
        # Simple 2x2x2 cube
        cube_cells = []
        for x in range(2):
            for y in range(2):
                for z in range(2):
                    cube_cells.append((x, y, z))
        
        symmetries = container_symmetry_group(cube_cells)
        # A cube should have significant symmetry
        self.assertGreater(len(symmetries), 1)
        self.assertLessEqual(len(symmetries), 24)
    
    def test_container_symmetry_group_asymmetric(self):
        """Test symmetry group for asymmetric container."""
        # L-shaped container with minimal symmetry
        cells = [(0,0,0), (1,0,0), (0,1,0)]
        symmetries = container_symmetry_group(cells)
        # Should have at least identity
        self.assertGreaterEqual(len(symmetries), 1)

if __name__ == '__main__':
    unittest.main()
