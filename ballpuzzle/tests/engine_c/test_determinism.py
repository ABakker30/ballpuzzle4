"""Determinism tests for Engine-C."""

import pytest
from src.solver.engines.engine_c.api_adapter import EngineCAdapter


def test_engine_c_deterministic_same_seed():
    """Test that Engine-C produces identical results with same seed."""
    engine = EngineCAdapter()
    
    # Simple 4-cell container
    container = {
        'coordinates': [
            [0, 0, 0],
            [0, 1, 0], 
            [1, 0, 0],
            [1, 1, 0]
        ]
    }
    
    # Load pieces
    from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
    pieces = load_fcc_A_to_Y()
    inventory = {'pieces': {'A': 1}}
    
    # Run twice with same seed
    seed = 12345
    options1 = {'seed': seed}
    options2 = {'seed': seed}
    
    events1 = list(engine.solve(container, inventory, pieces, options1))
    events2 = list(engine.solve(container, inventory, pieces, options2))
    
    # Should have same number of events
    assert len(events1) == len(events2)
    
    # Done events should have same metrics
    done1 = [e for e in events1 if e['type'] == 'done'][0]
    done2 = [e for e in events2 if e['type'] == 'done'][0]
    
    assert done1['metrics']['solutions'] == done2['metrics']['solutions']
    assert done1['metrics']['nodes'] == done2['metrics']['nodes']
    assert done1['metrics']['pruned'] == done2['metrics']['pruned']


def test_engine_c_different_seeds():
    """Test that Engine-C may produce different results with different seeds."""
    engine = EngineCAdapter()
    
    # Simple 4-cell container
    container = {
        'coordinates': [
            [0, 0, 0],
            [0, 1, 0], 
            [1, 0, 0],
            [1, 1, 0]
        ]
    }
    
    # Load pieces
    from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
    pieces = load_fcc_A_to_Y()
    inventory = {'pieces': {'A': 1}}
    
    # Run with different seeds
    options1 = {'seed': 12345}
    options2 = {'seed': 54321}
    
    events1 = list(engine.solve(container, inventory, pieces, options1))
    events2 = list(engine.solve(container, inventory, pieces, options2))
    
    # Both should complete successfully
    assert len(events1) >= 1
    assert len(events2) >= 1
    
    # Both should have done events
    done1 = [e for e in events1 if e['type'] == 'done']
    done2 = [e for e in events2 if e['type'] == 'done']
    
    assert len(done1) == 1
    assert len(done2) == 1
    
    # Seeds should be recorded correctly
    assert done1[0]['metrics']['seed'] == 12345
    assert done2[0]['metrics']['seed'] == 54321
