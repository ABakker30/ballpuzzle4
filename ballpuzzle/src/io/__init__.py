"""Input/output handling with schema validation for ball puzzle data.

This module provides I/O functionality for containers, pieces, solutions,
and snapshots with JSON schema validation.
"""

from .container import load_container
from .solution import write_solution
from .snapshot import open_eventlog, write_event

__all__ = ["load_container", "write_solution", "open_eventlog", "write_event"]
