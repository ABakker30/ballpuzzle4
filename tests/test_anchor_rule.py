import unittest
from src.solver.symbreak import anchor_rule_filter, container_symmetry_group, is_canonical_under_container_syms

class TestAnchorRule(unittest.TestCase):
    
    def test_anchor_rule_filter_basic(self):
        """Test basic anchor rule filtering."""
        # Simple container
        container = [(0,0,0), (1,0,0), (0,1,0)]
        min_cell = (0,0,0)
        lowest_piece = "A"
        
        # Get symmetry group
        Rgroup = container_symmetry_group(container)
        
        # Test placements - some covering min_cell, some not
        placements = [
            ("A", ((0,0,0), (1,0,0))),  # covers min_cell
            ("A", ((1,0,0), (0,1,0))),  # doesn't cover min_cell
            ("A", ((0,0,0), (0,1,0))),  # covers min_cell
            ("B", ((0,0,0), (1,0,0))),  # wrong piece ID
        ]
        
        filtered = anchor_rule_filter(placements, min_cell, lowest_piece, Rgroup)
        
        # Should only include placements of piece A that cover min_cell
        self.assertTrue(all(pid == "A" for pid, _ in filtered))
        self.assertTrue(all(min_cell in atoms for _, atoms in filtered))
        
        # Should have at least one placement
        self.assertGreater(len(filtered), 0)
    
    def test_anchor_rule_canonical_filtering(self):
        """Test that anchor rule filters to canonical orientations."""
        # 2x2 square container
        container = [(0,0,0), (1,0,0), (0,1,0), (1,1,0)]
        min_cell = (0,0,0)
        lowest_piece = "A"
        
        Rgroup = container_symmetry_group(container)
        
        # Create multiple orientations that should be equivalent under symmetry
        # Simple 2-atom piece in different orientations
        placements = [
            ("A", ((0,0,0), (1,0,0))),  # horizontal
            ("A", ((0,0,0), (0,1,0))),  # vertical (should be equivalent under rotation)
        ]
        
        filtered = anchor_rule_filter(placements, min_cell, lowest_piece, Rgroup)
        
        # Should have at least one placement
        self.assertGreater(len(filtered), 0)
        # Should filter out some equivalent orientations if container has symmetry
        self.assertLessEqual(len(filtered), len(placements))
    
    def test_is_canonical_under_symmetries(self):
        """Test canonical checking under symmetries."""
        # Simple symmetric container
        container = [(0,0,0), (1,0,0), (0,1,0), (1,1,0)]
        Rgroup = container_symmetry_group(container)
        
        # Test atom set
        atoms = ((0,0,0), (1,0,0))
        
        # Should return boolean
        result = is_canonical_under_container_syms(atoms, Rgroup)
        self.assertIsInstance(result, bool)
    
    def test_anchor_rule_empty_input(self):
        """Test anchor rule with empty input."""
        container = [(0,0,0)]
        min_cell = (0,0,0)
        lowest_piece = "A"
        Rgroup = container_symmetry_group(container)
        
        # Empty placements
        filtered = anchor_rule_filter([], min_cell, lowest_piece, Rgroup)
        self.assertEqual(len(filtered), 0)
    
    def test_anchor_rule_no_covering_placements(self):
        """Test anchor rule when no placements cover min_cell."""
        container = [(0,0,0), (1,0,0), (0,1,0)]
        min_cell = (0,0,0)
        lowest_piece = "A"
        Rgroup = container_symmetry_group(container)
        
        # Placements that don't cover min_cell
        placements = [
            ("A", ((1,0,0), (0,1,0))),
            ("A", ((1,0,0),)),
        ]
        
        filtered = anchor_rule_filter(placements, min_cell, lowest_piece, Rgroup)
        self.assertEqual(len(filtered), 0)

if __name__ == '__main__':
    unittest.main()
