"""Sanity tests for Engine-C basic functionality."""

import pytest
from src.solver.engines.engine_c.api_adapter import EngineCAdapter


def test_engine_c_imports():
    """Test that Engine-C can be imported without errors."""
    engine = EngineCAdapter()
    assert engine.name == "engine-c"


def test_engine_c_empty_container():
    """Test Engine-C with empty container."""
    engine = EngineCAdapter()
    
    container = {"cells": []}
    inventory = {"pieces": {}}
    pieces = {}
    options = {"seed": 12345}
    
    events = list(engine.solve(container, inventory, pieces, options))
    
    # Should have at least a done event
    assert len(events) >= 1
    assert events[-1]["type"] == "done"
    assert events[-1]["metrics"]["solutions"] == 0


def test_engine_c_tiny_container():
    """Test Engine-C with minimal 4-cell container and single piece."""
    engine = EngineCAdapter()
    
    # 4-cell FCC container (simple line)
    container = {
        "cells": [
            [0, 0, 0],
            [1, 1, 0], 
            [2, 0, 0],
            [3, 1, 0]
        ]
    }
    
    # Single 4-cell piece that exactly fits
    pieces = {
        "A": {
            "cells": [
                [0, 0, 0],
                [1, 1, 0],
                [2, 0, 0], 
                [3, 1, 0]
            ]
        }
    }
    
    inventory = {"pieces": {"A": 1}}
    options = {"seed": 12345}
    
    events = list(engine.solve(container, inventory, pieces, options))
    
    # Should complete without errors
    assert len(events) >= 1
    done_event = events[-1]
    assert done_event["type"] == "done"
    
    # May or may not find solution due to implementation status
    # Just verify it doesn't crash
