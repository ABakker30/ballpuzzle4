import json
from jsonschema import validate
from pathlib import Path
from typing import Any, Dict, List, Tuple
from .schema import load_schema
from ..coords.canonical import cid_sha256

I3 = Tuple[int,int,int]

def load_container(path: str) -> Dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(instance=data, schema=load_schema("container.schema.json"))
    # Ensure canonical CID
    cells: List[I3] = [tuple(map(int, c)) for c in data["coordinates"]]
    cid = cid_sha256(cells)
    data["cid_sha256"] = cid
    return data
