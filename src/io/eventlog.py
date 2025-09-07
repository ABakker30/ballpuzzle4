"""Event logging for tracking solver operations and debugging."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum


class EventLevel(Enum):
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventLogger:
    """Structured event logger for ball puzzle solver operations."""
    
    def __init__(self, log_file: Optional[str] = None, console_output: bool = True):
        """Initialize event logger.
        
        Args:
            log_file: Optional file path for logging
            console_output: Whether to output to console
        """
        self.log_file = log_file
        self.console_output = console_output
        self.events = []
        
        # Set up Python logger
        self.logger = logging.getLogger("ballpuzzle")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add console handler if requested
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if requested
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_event(
        self,
        level: EventLevel,
        event_type: str,
        message: str,
        data: Dict[str, Any] = None
    ):
        """Log a structured event.
        
        Args:
            level: Event severity level
            event_type: Type of event (e.g., "solver_start", "piece_placed")
            message: Human-readable message
            data: Optional structured data
        """
        if data is None:
            data = {}
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'event_type': event_type,
            'message': message,
            'data': data
        }
        
        self.events.append(event)
        
        # Log to Python logger
        log_level = getattr(logging, level.value.upper())
        self.logger.log(log_level, f"[{event_type}] {message}")
    
    def debug(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Log debug event."""
        self.log_event(EventLevel.DEBUG, event_type, message, data)
    
    def info(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Log info event."""
        self.log_event(EventLevel.INFO, event_type, message, data)
    
    def warning(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Log warning event."""
        self.log_event(EventLevel.WARNING, event_type, message, data)
    
    def error(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Log error event."""
        self.log_event(EventLevel.ERROR, event_type, message, data)
    
    def critical(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Log critical event."""
        self.log_event(EventLevel.CRITICAL, event_type, message, data)
    
    def log_solver_start(self, engine: str, container_size: int, piece_count: int):
        """Log solver start event."""
        self.info("solver_start", f"Starting solver with {engine} engine", {
            'engine': engine,
            'container_size': container_size,
            'piece_count': piece_count
        })
    
    def log_solver_finish(self, status: str, time_elapsed: float, nodes_explored: int):
        """Log solver finish event."""
        self.info("solver_finish", f"Solver finished with status: {status}", {
            'status': status,
            'time_elapsed': time_elapsed,
            'nodes_explored': nodes_explored
        })
    
    def log_piece_placed(self, piece_name: str, coordinates: list, depth: int):
        """Log piece placement event."""
        self.debug("piece_placed", f"Placed piece {piece_name} at depth {depth}", {
            'piece_name': piece_name,
            'coordinates': coordinates,
            'depth': depth
        })
    
    def log_piece_backtrack(self, piece_name: str, depth: int):
        """Log piece backtrack event."""
        self.debug("piece_backtrack", f"Backtracked piece {piece_name} at depth {depth}", {
            'piece_name': piece_name,
            'depth': depth
        })
    
    def log_pruning(self, reason: str, depth: int):
        """Log pruning event."""
        self.debug("pruning", f"Pruned branch: {reason}", {
            'reason': reason,
            'depth': depth
        })
    
    def log_solution_found(self, solution_id: str, piece_count: int):
        """Log solution found event."""
        self.info("solution_found", f"Solution found with {piece_count} pieces", {
            'solution_id': solution_id,
            'piece_count': piece_count
        })
    
    def save_events(self, file_path: str):
        """Save all events to JSON file.
        
        Args:
            file_path: Path where to save events
        """
        with open(file_path, 'w') as f:
            json.dump(self.events, f, indent=2)
    
    def clear_events(self):
        """Clear all stored events."""
        self.events.clear()
    
    def get_events(self, event_type: str = None, level: EventLevel = None) -> list:
        """Get filtered events.
        
        Args:
            event_type: Optional event type filter
            level: Optional level filter
            
        Returns:
            List of matching events
        """
        filtered_events = self.events
        
        if event_type:
            filtered_events = [e for e in filtered_events if e['event_type'] == event_type]
        
        if level:
            filtered_events = [e for e in filtered_events if e['level'] == level.value]
        
        return filtered_events
