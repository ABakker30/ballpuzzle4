import json
from jsonschema import validate
from pathlib import Path
from typing import Any, Dict, List, Tuple
from .schema import load_schema
from ..coords.canonical import cid_sha256

I3 = Tuple[int,int,int]

def load_container(path: str) -> Dict[str, Any]:
    """Load and validate v1.0 container file.
    
    Only accepts Container Standard v1.0 format with:
    - version: "1.0"
    - lattice: "fcc" 
    - cells: array of [i,j,k] triplets
    - cid: "sha256:..." format
    - designer: object with name, date, optional email
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    
    # Quick format check before schema validation
    if data.get("version") != "1.0":
        raise ValueError(
            f"Unsupported container version: {data.get('version')}. "
            "Only v1.0 containers are supported. Legacy formats are deprecated."
        )
    
    # Validate against v1.0 schema
    validate(instance=data, schema=load_schema("container.schema.json"))
    
    # Use cells field (v1.0 format) instead of coordinates (legacy)
    if "cells" not in data:
        raise ValueError("v1.0 containers must have 'cells' field, not 'coordinates'")
    
    cells: List[I3] = [tuple(map(int, c)) for c in data["cells"]]
    cid = cid_sha256(cells)
    data["cid_sha256"] = cid
    
    # Map cells to coordinates for backward compatibility with existing engine code
    data["coordinates"] = data["cells"]
    
    return data
