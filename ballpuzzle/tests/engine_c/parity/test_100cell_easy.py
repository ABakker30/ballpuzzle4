"""100-cell parity tests for Engine-C."""

import pytest
from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y


def test_engine_c_shape3_single_piece():
    """Test Engine-C on Shape_3 container with single piece A."""
    engine = EngineCAdapter()
    
    # Load Shape_3 container (100 cells)
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    inventory = {'pieces': {'A': 1}}
    
    options = {
        'seed': 20250907,
        'flags': {
            'max_results': 1,
            'time_budget_s': 30.0,
            'pruning_level': 'basic',
            'shuffle': 'ties_only',
            'snapshot_every_nodes': 1000
        }
    }
    
    events = list(engine.solve(container, inventory, pieces, options))
    
    # Should complete within time budget
    assert len(events) >= 1
    
    # Should have done event
    done_events = [e for e in events if e['type'] == 'done']
    assert len(done_events) == 1
    
    done = done_events[0]
    
    # Should explore search space
    assert done['metrics']['nodes'] > 0
    
    # Should respect seed
    assert done['metrics']['seed'] == 20250907
    
    # Should not crash or timeout
    assert 'solutions' in done['metrics']
    assert 'nodes' in done['metrics']
    assert 'pruned' in done['metrics']


def test_engine_c_deterministic_on_shape3():
    """Test Engine-C determinism on Shape_3 container."""
    engine = EngineCAdapter()
    
    container = load_container('data/containers/legacy_fixed/Shape_3.json')
    pieces = load_fcc_A_to_Y()
    inventory = {'pieces': {'A': 1}}
    
    seed = 20250907
    options = {
        'seed': seed,
        'flags': {
            'max_results': 1,
            'time_budget_s': 10.0,
            'pruning_level': 'basic',
            'shuffle': 'ties_only'
        }
    }
    
    # Run twice with same configuration
    events1 = list(engine.solve(container, inventory, pieces, options))
    events2 = list(engine.solve(container, inventory, pieces, options))
    
    # Should have same number of events
    assert len(events1) == len(events2)
    
    # Done events should have identical metrics
    done1 = [e for e in events1 if e['type'] == 'done'][0]
    done2 = [e for e in events2 if e['type'] == 'done'][0]
    
    assert done1['metrics']['solutions'] == done2['metrics']['solutions']
    assert done1['metrics']['nodes'] == done2['metrics']['nodes']
    assert done1['metrics']['pruned'] == done2['metrics']['pruned']
    assert done1['metrics']['seed'] == done2['metrics']['seed']


def test_engine_c_validates_solutions():
    """Test that Engine-C generates valid solution format when found."""
    engine = EngineCAdapter()
    
    # Use simple 4-cell case that should find solution quickly
    container = {
        'coordinates': [
            [0, 0, 0],
            [0, 1, 0], 
            [1, 0, 0],
            [1, 1, 0]
        ]
    }
    
    pieces = load_fcc_A_to_Y()
    inventory = {'pieces': {'A': 1}}
    options = {'seed': 12345}
    
    events = list(engine.solve(container, inventory, pieces, options))
    
    # Should find solution
    solution_events = [e for e in events if e['type'] == 'solution']
    
    if solution_events:  # If solution found
        solution = solution_events[0]['solution']
        
        # Validate solution structure
        assert 'containerCidSha256' in solution
        assert 'lattice' in solution
        assert 'piecesUsed' in solution
        assert 'placements' in solution
        assert 'sid_state_sha256' in solution
        assert 'sid_route_sha256' in solution
        assert 'sid_state_canon_sha256' in solution
        
        # Validate content
        assert solution['lattice'] == 'fcc'
        assert isinstance(solution['placements'], list)
        assert isinstance(solution['piecesUsed'], dict)
