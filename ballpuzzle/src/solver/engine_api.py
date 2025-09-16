"""Engine protocol and types for the tight scope M2 task."""

from typing import Protocol, Iterator, Dict, Any, TypedDict

class EngineOptions(TypedDict, total=False):
    seed: int
    flags: Dict[str, Any]

class SolveEvent(TypedDict, total=False):
    t_ms: int
    type: str
    metrics: Dict[str, Any]
    solution: Dict[str, Any]

class EngineProtocol(Protocol):
    name: str
    
    def solve(self, container: Dict[str, Any], inventory: Dict[str, Any], 
              pieces: Dict[str, Any], options: EngineOptions) -> Iterator[SolveEvent]:
        ...
