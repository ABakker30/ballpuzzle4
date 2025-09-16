import json
from typing import Dict, Any, TextIO

def open_eventlog(path: str):
    return open(path, "w", encoding="utf-8")

def write_event(line: Dict[str, Any], fp: TextIO):
    fp.write(json.dumps({"v":1, **line}, ensure_ascii=False) + "\n")
