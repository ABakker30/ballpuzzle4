"""Bitmap-based state representation for DLX engine optimization."""

from typing import List, Set, Dict, Tuple
import sys

class BitmapState:
    """Efficient bitmap-based state management for Algorithm X."""
    
    def __init__(self, num_columns: int, num_rows: int):
        self.num_columns = num_columns
        self.num_rows = num_rows
        
        # Column state: each bit represents whether a column is active
        self.active_columns = (1 << num_columns) - 1  # All columns initially active
        
        # Row state: each bit represents whether a row is active
        self.active_rows = (1 << num_rows) - 1  # All rows initially active
        
        # Precomputed row-to-column mappings (row_id -> column_bitmap)
        self.row_columns: Dict[int, int] = {}
        
        # Column-to-rows mappings (column_id -> row_bitmap)
        self.column_rows: List[int] = [0] * num_columns
        
    def set_row_columns(self, row_id: int, column_ids: List[int]):
        """Set which columns a row covers."""
        if row_id >= self.num_rows:
            return
            
        # Convert column list to bitmap
        column_bitmap = 0
        for col_id in column_ids:
            if col_id < self.num_columns:
                column_bitmap |= (1 << col_id)
                # Update column-to-rows mapping
                self.column_rows[col_id] |= (1 << row_id)
        
        self.row_columns[row_id] = column_bitmap
    
    def is_column_active(self, col_id: int) -> bool:
        """Check if a column is active."""
        return bool(self.active_columns & (1 << col_id))
    
    def is_row_active(self, row_id: int) -> bool:
        """Check if a row is active."""
        return bool(self.active_rows & (1 << row_id))
    
    def get_active_columns(self) -> List[int]:
        """Get list of active column IDs."""
        active = []
        for i in range(self.num_columns):
            if self.active_columns & (1 << i):
                active.append(i)
        return active
    
    def get_active_rows(self) -> List[int]:
        """Get list of active row IDs."""
        active = []
        for i in range(self.num_rows):
            if self.active_rows & (1 << i):
                active.append(i)
        return active
    
    def get_column_candidates(self, col_id: int) -> List[int]:
        """Get active rows that cover a specific column."""
        if not self.is_column_active(col_id):
            return []
        
        # Get rows that cover this column AND are still active
        column_row_bitmap = self.column_rows[col_id]
        active_candidates_bitmap = column_row_bitmap & self.active_rows
        
        candidates = []
        for i in range(self.num_rows):
            if active_candidates_bitmap & (1 << i):
                candidates.append(i)
        return candidates
    
    def count_column_candidates(self, col_id: int) -> int:
        """Count active rows that cover a specific column."""
        if not self.is_column_active(col_id):
            return 0
        
        column_row_bitmap = self.column_rows[col_id]
        active_candidates_bitmap = column_row_bitmap & self.active_rows
        
        # Count set bits using Brian Kernighan's algorithm
        count = 0
        while active_candidates_bitmap:
            active_candidates_bitmap &= active_candidates_bitmap - 1
            count += 1
        return count
    
    def choose_best_column(self) -> Tuple[int, int]:
        """Choose column with minimum candidates (MRV heuristic)."""
        best_col = -1
        best_count = sys.maxsize
        
        for col_id in range(self.num_columns):
            if self.is_column_active(col_id):
                count = self.count_column_candidates(col_id)
                if count < best_count:
                    best_count = count
                    best_col = col_id
                    if count <= 1:  # Early termination for optimal case
                        break
        
        return best_col, best_count
    
    def cover_column(self, col_id: int) -> Tuple[int, int]:
        """Cover a column and return bitmaps of removed columns and rows."""
        if not self.is_column_active(col_id):
            return 0, 0
        
        # Remove the column
        removed_columns = 1 << col_id
        self.active_columns &= ~removed_columns
        
        # Remove all rows that cover this column
        column_row_bitmap = self.column_rows[col_id]
        removed_rows = column_row_bitmap & self.active_rows
        self.active_rows &= ~removed_rows
        
        return removed_columns, removed_rows
    
    def cover_row(self, row_id: int) -> Tuple[int, int]:
        """Cover a row and return bitmaps of removed columns and rows."""
        if not self.is_row_active(row_id):
            return 0, 0
        
        # Get columns covered by this row
        row_column_bitmap = self.row_columns.get(row_id, 0)
        
        removed_columns = 0
        removed_rows = 0
        
        # For each column covered by this row
        for col_id in range(self.num_columns):
            if row_column_bitmap & (1 << col_id):
                if self.is_column_active(col_id):
                    # Remove the column
                    removed_columns |= (1 << col_id)
                    self.active_columns &= ~(1 << col_id)
                    
                    # Remove all rows that cover this column
                    column_row_bitmap = self.column_rows[col_id]
                    rows_to_remove = column_row_bitmap & self.active_rows
                    removed_rows |= rows_to_remove
                    self.active_rows &= ~rows_to_remove
        
        return removed_columns, removed_rows
    
    def uncover(self, removed_columns: int, removed_rows: int):
        """Restore previously removed columns and rows."""
        self.active_columns |= removed_columns
        self.active_rows |= removed_rows
    
    def is_solved(self) -> bool:
        """Check if all columns are covered (no active columns)."""
        return self.active_columns == 0
    
    def has_empty_column(self) -> bool:
        """Check if any active column has no candidates."""
        for col_id in range(self.num_columns):
            if self.is_column_active(col_id):
                if self.count_column_candidates(col_id) == 0:
                    return True
        return False
    
    def get_stats(self) -> Dict:
        """Get state statistics for debugging."""
        active_cols = bin(self.active_columns).count('1')
        active_rows_count = bin(self.active_rows).count('1')
        
        return {
            "active_columns": active_cols,
            "active_rows": active_rows_count,
            "total_columns": self.num_columns,
            "total_rows": self.num_rows,
            "coverage": (self.num_columns - active_cols) / self.num_columns * 100
        }
