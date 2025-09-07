from typing import Dict
from .engine_api import EngineProtocol
from .engines.current_engine import CurrentEngine
from .engines.dfs_engine import DFSEngine

_REGISTRY: Dict[str, EngineProtocol] = {
    "current": CurrentEngine(),
    "dfs": DFSEngine(),
}

def get_engine(name: str) -> EngineProtocol:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise SystemExit(f"--engine must be one of: {', '.join(_REGISTRY.keys())}")
