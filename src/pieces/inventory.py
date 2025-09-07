from typing import Dict

class PieceBag:
    def __init__(self, counts: Dict[str,int]):
        self.counts = {k:int(v) for k,v in counts.items() if int(v) > 0}

    @classmethod
    def from_dict(cls, d: Dict[str,int]):
        return cls(d)

    def to_dict(self) -> Dict[str,int]:
        return dict(self.counts)
