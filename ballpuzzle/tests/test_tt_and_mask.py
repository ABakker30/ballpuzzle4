import unittest
from src.solver.tt import OccMask, SeenMasks

class TestOccMaskAndTT(unittest.TestCase):
    
    def test_occ_mask_creation(self):
        """Test OccMask creation and initialization."""
        cells = [(0,0,0), (1,0,0), (0,1,0)]
        mask = OccMask(cells)
        
        # Should start with empty mask
        self.assertEqual(mask.mask, 0)
        self.assertEqual(mask.popcount(), 0)
        
        # Should have correct cell ordering
        self.assertEqual(len(mask.order), 3)
        self.assertIn((0,0,0), mask.order)
        self.assertIn((1,0,0), mask.order)
        self.assertIn((0,1,0), mask.order)
    
    def test_occ_mask_set_cells(self):
        """Test setting cells in occupancy mask."""
        cells = [(0,0,0), (1,0,0), (0,1,0)]
        mask = OccMask(cells)
        
        # Set single cell
        mask.set_cells([(0,0,0)])
        self.assertEqual(mask.popcount(), 1)
        self.assertNotEqual(mask.mask, 0)
        
        # Set multiple cells
        mask.set_cells([(1,0,0), (0,1,0)])
        self.assertEqual(mask.popcount(), 3)  # All cells set
    
    def test_occ_mask_clear_cells(self):
        """Test clearing cells in occupancy mask."""
        cells = [(0,0,0), (1,0,0), (0,1,0)]
        mask = OccMask(cells)
        
        # Set all cells first
        mask.set_cells(cells)
        self.assertEqual(mask.popcount(), 3)
        
        # Clear one cell
        mask.clear_cells([(0,0,0)])
        self.assertEqual(mask.popcount(), 2)
        
        # Clear remaining cells
        mask.clear_cells([(1,0,0), (0,1,0)])
        self.assertEqual(mask.popcount(), 0)
        self.assertEqual(mask.mask, 0)
    
    def test_occ_mask_clone(self):
        """Test cloning occupancy mask."""
        cells = [(0,0,0), (1,0,0), (0,1,0)]
        mask1 = OccMask(cells)
        mask1.set_cells([(0,0,0), (1,0,0)])
        
        # Clone the mask
        mask2 = mask1.clone()
        
        # Should have same state
        self.assertEqual(mask1.mask, mask2.mask)
        self.assertEqual(mask1.popcount(), mask2.popcount())
        self.assertEqual(mask1.order, mask2.order)
        
        # Should be independent copies
        mask2.set_cells([(0,1,0)])
        self.assertNotEqual(mask1.mask, mask2.mask)
    
    def test_occ_mask_bit_operations(self):
        """Test bitwise operations work correctly."""
        cells = [(0,0,0), (1,0,0), (0,1,0), (1,1,0)]
        mask = OccMask(cells)
        
        # Test setting specific pattern
        mask.set_cells([(0,0,0), (1,1,0)])  # corners
        count1 = mask.popcount()
        
        mask.set_cells([(1,0,0)])  # add one more
        count2 = mask.popcount()
        
        self.assertEqual(count2, count1 + 1)
        
        # Test clearing
        mask.clear_cells([(0,0,0)])
        count3 = mask.popcount()
        self.assertEqual(count3, count2 - 1)
    
    def test_seen_masks_basic(self):
        """Test basic SeenMasks functionality."""
        seen = SeenMasks()
        
        # First time should be new
        self.assertTrue(seen.check_and_add(123))
        
        # Second time should be seen
        self.assertFalse(seen.check_and_add(123))
        
        # Different mask should be new
        self.assertTrue(seen.check_and_add(456))
    
    def test_seen_masks_multiple(self):
        """Test SeenMasks with multiple values."""
        seen = SeenMasks()
        
        masks = [1, 2, 4, 8, 16, 32]
        
        # All should be new first time
        for mask in masks:
            self.assertTrue(seen.check_and_add(mask))
        
        # All should be seen second time
        for mask in masks:
            self.assertFalse(seen.check_and_add(mask))
    
    def test_integration_mask_with_seen(self):
        """Test integration of OccMask with SeenMasks."""
        cells = [(0,0,0), (1,0,0), (0,1,0)]
        seen = SeenMasks()
        
        # Create different mask states
        mask1 = OccMask(cells)
        mask1.set_cells([(0,0,0)])
        
        mask2 = OccMask(cells)
        mask2.set_cells([(1,0,0)])
        
        mask3 = OccMask(cells)
        mask3.set_cells([(0,0,0)])  # Same as mask1
        
        # Check with SeenMasks
        self.assertTrue(seen.check_and_add(mask1.mask))
        self.assertTrue(seen.check_and_add(mask2.mask))
        self.assertFalse(seen.check_and_add(mask3.mask))  # Same as mask1
    
    def test_occ_mask_empty_cells(self):
        """Test OccMask with empty cell list."""
        mask = OccMask([])
        self.assertEqual(mask.mask, 0)
        self.assertEqual(mask.popcount(), 0)
        self.assertEqual(len(mask.order), 0)
    
    def test_occ_mask_single_cell(self):
        """Test OccMask with single cell."""
        cells = [(5,3,1)]
        mask = OccMask(cells)
        
        mask.set_cells([(5,3,1)])
        self.assertEqual(mask.popcount(), 1)
        self.assertEqual(mask.mask, 1)  # Should be bit 0
        
        mask.clear_cells([(5,3,1)])
        self.assertEqual(mask.popcount(), 0)
        self.assertEqual(mask.mask, 0)

if __name__ == '__main__':
    unittest.main()
