"""Core solving engines and algorithms for ball puzzle solving.

This module provides the main solving infrastructure including
engine APIs, heuristics, pruning strategies, and symmetry breaking.
"""

from .engine_api import EngineProtocol, EngineOptions, SolveEvent
from .engines.current_engine import CurrentEngine
from .engines.dfs_engine import DFSEngine
from .registry import get_engine

__all__ = [
    "EngineProtocol",
    "EngineOptions", 
    "SolveEvent",
    "CurrentEngine",
    "DFSEngine",
    "get_engine"
]
