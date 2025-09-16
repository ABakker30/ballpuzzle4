import unittest
from src.solver.heuristics import tie_shuffle

class TestTieShuffle(unittest.TestCase):
    
    def test_tie_shuffle_no_seed(self):
        """Test tie_shuffle with no seed returns identity."""
        items = [1, 2, 3, 4, 5]
        result = tie_shuffle(items, None)
        
        # Should return the same list (identity)
        self.assertEqual(result, items)
        
        # Should be a different object (copy)
        self.assertIsNot(result, items)
    
    def test_tie_shuffle_with_seed_deterministic(self):
        """Test tie_shuffle with seed is deterministic."""
        items = [1, 2, 3, 4, 5]
        seed = 42
        
        # Multiple calls with same seed should give same result
        result1 = tie_shuffle(items, seed)
        result2 = tie_shuffle(items, seed)
        
        self.assertEqual(result1, result2)
    
    def test_tie_shuffle_different_seeds(self):
        """Test tie_shuffle with different seeds gives different results."""
        items = list(range(20))  # Larger list for better shuffle visibility
        
        result1 = tie_shuffle(items, 42)
        result2 = tie_shuffle(items, 123)
        
        # Should be different (very high probability)
        self.assertNotEqual(result1, result2)
        
        # But should contain same elements
        self.assertEqual(sorted(result1), sorted(items))
        self.assertEqual(sorted(result2), sorted(items))
    
    def test_tie_shuffle_preserves_elements(self):
        """Test that tie_shuffle preserves all elements."""
        items = ['a', 'b', 'c', 'd', 'e', 'f']
        seed = 999
        
        result = tie_shuffle(items, seed)
        
        # Should have same length
        self.assertEqual(len(result), len(items))
        
        # Should contain all original elements
        self.assertEqual(sorted(result), sorted(items))
    
    def test_tie_shuffle_empty_list(self):
        """Test tie_shuffle with empty list."""
        items = []
        
        # With no seed
        result1 = tie_shuffle(items, None)
        self.assertEqual(result1, [])
        
        # With seed
        result2 = tie_shuffle(items, 42)
        self.assertEqual(result2, [])
    
    def test_tie_shuffle_single_element(self):
        """Test tie_shuffle with single element."""
        items = [42]
        
        # With no seed
        result1 = tie_shuffle(items, None)
        self.assertEqual(result1, [42])
        
        # With seed
        result2 = tie_shuffle(items, 123)
        self.assertEqual(result2, [42])
    
    def test_tie_shuffle_different_types(self):
        """Test tie_shuffle with different element types."""
        # Test with strings
        strings = ['apple', 'banana', 'cherry']
        result_str = tie_shuffle(strings, 42)
        self.assertEqual(sorted(result_str), sorted(strings))
        
        # Test with tuples
        tuples = [(1,2), (3,4), (5,6)]
        result_tup = tie_shuffle(tuples, 42)
        self.assertEqual(sorted(result_tup), sorted(tuples))
        
        # Test with mixed types
        mixed = [1, 'a', (2,3), None]
        result_mix = tie_shuffle(mixed, 42)
        self.assertEqual(len(result_mix), len(mixed))
        # Can't easily sort mixed types, but check all elements present
        for item in mixed:
            self.assertIn(item, result_mix)
    
    def test_tie_shuffle_reproducibility(self):
        """Test that tie_shuffle is reproducible across multiple runs."""
        items = list(range(10))
        seed = 12345
        
        # Get reference result
        reference = tie_shuffle(items, seed)
        
        # Test multiple times
        for _ in range(10):
            result = tie_shuffle(items, seed)
            self.assertEqual(result, reference)
    
    def test_tie_shuffle_zero_seed(self):
        """Test tie_shuffle with zero seed."""
        items = [1, 2, 3, 4, 5]
        
        result1 = tie_shuffle(items, 0)
        result2 = tie_shuffle(items, 0)
        
        # Should be deterministic even with zero seed
        self.assertEqual(result1, result2)
        self.assertEqual(sorted(result1), sorted(items))

if __name__ == '__main__':
    unittest.main()
