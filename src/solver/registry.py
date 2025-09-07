from typing import Dict
from .engine_api import EngineProtocol
from .engines.current_engine import CurrentEngine
from .engines.dfs_engine import DFSEngine
from .engines.dlx_engine import DLXEngine
from .engines.legacy_engine import LegacyEngine
from .engines.engine_c import EngineCAdapter

_REGISTRY: Dict[str, EngineProtocol] = {
    "current": CurrentEngine(),
    "dfs": DFSEngine(),
    "dlx": DLXEngine(),
    "legacy": LegacyEngine(),
    "engine-c": EngineCAdapter(),
}

def get_engine(name: str) -> EngineProtocol:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise SystemExit(f"--engine must be one of: {', '.join(_REGISTRY.keys())}")
