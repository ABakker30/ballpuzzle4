import json, importlib.resources as r

def load_schema(name: str):
    with r.files(__package__).joinpath(name).open("r", encoding="utf-8") as f:
        return json.load(f)
