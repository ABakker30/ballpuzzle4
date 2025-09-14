#!/usr/bin/env python3
"""
Restore DLX engine from backup.
"""

import shutil

# Copy the working DLX engine from refactored version
shutil.copy(
    "C:/Ball Puzzle/ballpuzzle/src/solver/engines/dlx_engine_refactored.py",
    "C:/Ball Puzzle/ballpuzzle/src/solver/engines/dlx_engine_backup.py"
)

print("DLX engine backed up to dlx_engine_backup.py")
