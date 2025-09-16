from typing import Dict

class PieceBag:
    def __init__(self, counts: Dict[str,int]):
        self.counts = {k:int(v) for k,v in counts.items() if int(v) > 0}

    @classmethod
    def from_dict(cls, d: Dict[str,int]):
        return cls(d)

    def to_dict(self) -> Dict[str,int]:
        return dict(self.counts)
    
    def get_count(self, piece: str) -> int:
        """Get current count of a piece."""
        return self.counts.get(piece, 0)
    
    def use_piece(self, piece: str, count: int = 1) -> bool:
        """Use a piece if available. Returns True if successful."""
        if self.counts.get(piece, 0) >= count:
            self.counts[piece] -= count
            if self.counts[piece] == 0:
                del self.counts[piece]
            return True
        return False
    
    def return_piece(self, piece: str, count: int = 1):
        """Return a piece to inventory."""
        self.counts[piece] = self.counts.get(piece, 0) + count
