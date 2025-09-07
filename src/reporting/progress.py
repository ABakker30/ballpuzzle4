"""Progress tracking for long-running solver operations."""

from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import time
from tqdm import tqdm


@dataclass
class ProgressState:
    """Current progress state information."""
    
    current_step: int = 0
    total_steps: Optional[int] = None
    current_depth: int = 0
    max_depth: int = 0
    nodes_explored: int = 0
    solutions_found: int = 0
    time_elapsed: float = 0.0
    estimated_time_remaining: Optional[float] = None
    current_operation: str = ""
    status_message: str = ""


class ProgressTracker:
    """Tracks and reports progress of solver operations."""
    
    def __init__(self, 
                 update_callback: Optional[Callable[[ProgressState], None]] = None,
                 use_tqdm: bool = True,
                 update_interval: float = 1.0):
        """Initialize progress tracker.
        
        Args:
            update_callback: Optional callback for progress updates
            use_tqdm: Whether to use tqdm for console progress bars
            update_interval: Minimum seconds between updates
        """
        self.update_callback = update_callback
        self.use_tqdm = use_tqdm
        self.update_interval = update_interval
        
        self.state = ProgressState()
        self._start_time: Optional[float] = None
        self._last_update_time: float = 0.0
        self._progress_bar: Optional[tqdm] = None
        
    def start(self, total_steps: Optional[int] = None, description: str = "Solving"):
        """Start progress tracking.
        
        Args:
            total_steps: Total number of steps (if known)
            description: Description for progress display
        """
        self._start_time = time.time()
        self._last_update_time = self._start_time
        
        self.state = ProgressState()
        self.state.total_steps = total_steps
        self.state.current_operation = description
        
        if self.use_tqdm:
            self._progress_bar = tqdm(
                total=total_steps,
                desc=description,
                unit="nodes" if total_steps is None else "steps",
                dynamic_ncols=True
            )
    
    def update(self, 
               step_increment: int = 1,
               current_depth: Optional[int] = None,
               nodes_explored_increment: int = 0,
               solutions_found_increment: int = 0,
               status_message: str = "",
               force_update: bool = False):
        """Update progress state.
        
        Args:
            step_increment: Number of steps to increment
            current_depth: Current search depth
            nodes_explored_increment: Number of nodes explored since last update
            solutions_found_increment: Number of solutions found since last update
            status_message: Current status message
            force_update: Force update even if interval hasn't elapsed
        """
        current_time = time.time()
        
        # Update state
        self.state.current_step += step_increment
        if current_depth is not None:
            self.state.current_depth = current_depth
            self.state.max_depth = max(self.state.max_depth, current_depth)
        
        self.state.nodes_explored += nodes_explored_increment
        self.state.solutions_found += solutions_found_increment
        
        if self._start_time is not None:
            self.state.time_elapsed = current_time - self._start_time
        
        if status_message:
            self.state.status_message = status_message
        
        # Calculate ETA if we have total steps
        if (self.state.total_steps is not None and 
            self.state.current_step > 0 and 
            self.state.time_elapsed > 0):
            
            rate = self.state.current_step / self.state.time_elapsed
            remaining_steps = self.state.total_steps - self.state.current_step
            self.state.estimated_time_remaining = remaining_steps / rate
        
        # Check if we should update display
        should_update = (force_update or 
                        current_time - self._last_update_time >= self.update_interval)
        
        if should_update:
            self._update_display()
            self._last_update_time = current_time
    
    def set_operation(self, operation: str):
        """Set current operation description.
        
        Args:
            operation: Operation description
        """
        self.state.current_operation = operation
        if self._progress_bar:
            self._progress_bar.set_description(operation)
    
    def finish(self, final_message: str = "Complete"):
        """Finish progress tracking.
        
        Args:
            final_message: Final status message
        """
        self.state.status_message = final_message
        self._update_display()
        
        if self._progress_bar:
            self._progress_bar.close()
            self._progress_bar = None
    
    def _update_display(self):
        """Update progress display."""
        # Update tqdm if available
        if self._progress_bar:
            # Create postfix with current stats
            postfix = {
                'depth': self.state.current_depth,
                'nodes': self.state.nodes_explored,
                'sols': self.state.solutions_found
            }
            
            if self.state.estimated_time_remaining:
                eta_mins = int(self.state.estimated_time_remaining // 60)
                eta_secs = int(self.state.estimated_time_remaining % 60)
                postfix['ETA'] = f"{eta_mins:02d}:{eta_secs:02d}"
            
            self._progress_bar.set_postfix(postfix)
            
            # Update progress bar position
            if self.state.total_steps is not None:
                self._progress_bar.n = self.state.current_step
            else:
                self._progress_bar.update(0)  # Just refresh display
            
            self._progress_bar.refresh()
        
        # Call custom callback if provided
        if self.update_callback:
            self.update_callback(self.state)
    
    def get_state(self) -> ProgressState:
        """Get current progress state.
        
        Returns:
            Current progress state
        """
        return self.state
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get progress summary.
        
        Returns:
            Dictionary with progress information
        """
        progress_percent = None
        if self.state.total_steps is not None and self.state.total_steps > 0:
            progress_percent = (self.state.current_step / self.state.total_steps) * 100
        
        return {
            'current_step': self.state.current_step,
            'total_steps': self.state.total_steps,
            'progress_percent': progress_percent,
            'current_depth': self.state.current_depth,
            'max_depth': self.state.max_depth,
            'nodes_explored': self.state.nodes_explored,
            'solutions_found': self.state.solutions_found,
            'time_elapsed': self.state.time_elapsed,
            'estimated_time_remaining': self.state.estimated_time_remaining,
            'current_operation': self.state.current_operation,
            'status_message': self.state.status_message
        }
