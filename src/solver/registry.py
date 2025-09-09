from typing import Dict
from .engine_api import EngineProtocol
from .engines.current_engine import CurrentEngine
from .engines.dfs_engine import DFSEngine
from .engines.dlx_engine import DLXEngine

ENGINES = {
    "dfs": DFSEngine(),
    "dlx": DLXEngine(),
}

def get_engine(name: str) -> EngineProtocol:
    try:
        return ENGINES[name]
    except KeyError:
        raise SystemExit(f"--engine must be one of: {', '.join(ENGINES.keys())}")
