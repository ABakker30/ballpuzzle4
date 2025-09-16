"""Metrics collection for solver performance analysis."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class SolverMetrics:
    """Container for solver performance metrics."""
    
    # Timing metrics
    start_time: float = 0.0
    end_time: float = 0.0
    total_time: float = 0.0
    
    # Search metrics
    nodes_explored: int = 0
    nodes_per_second: float = 0.0
    max_depth_reached: int = 0
    average_depth: float = 0.0
    
    # Pruning metrics
    pruned_nodes: int = 0
    pruning_rate: float = 0.0
    
    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    
    # Solution metrics
    solutions_found: int = 0
    first_solution_time: Optional[float] = None
    
    # Memory metrics
    peak_memory_usage: int = 0
    transposition_table_size: int = 0
    
    # Custom metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and analyzes solver performance metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = SolverMetrics()
        self.depth_samples: List[int] = []
        self.timing_checkpoints: List[Tuple[str, float]] = []
        self._start_time: Optional[float] = None
    
    def start_collection(self):
        """Start metrics collection."""
        self._start_time = time.time()
        self.metrics.start_time = self._start_time
        self.depth_samples.clear()
        self.timing_checkpoints.clear()
        self.timing_checkpoints.append(("start", self._start_time))
    
    def end_collection(self):
        """End metrics collection and calculate final metrics."""
        if self._start_time is None:
            return
        
        self.metrics.end_time = time.time()
        self.metrics.total_time = self.metrics.end_time - self.metrics.start_time
        
        # Calculate derived metrics
        if self.metrics.total_time > 0:
            self.metrics.nodes_per_second = self.metrics.nodes_explored / self.metrics.total_time
        
        if self.metrics.nodes_explored > 0:
            self.metrics.pruning_rate = self.metrics.pruned_nodes / (
                self.metrics.nodes_explored + self.metrics.pruned_nodes
            )
        
        cache_total = self.metrics.cache_hits + self.metrics.cache_misses
        if cache_total > 0:
            self.metrics.cache_hit_rate = self.metrics.cache_hits / cache_total
        
        if self.depth_samples:
            self.metrics.average_depth = sum(self.depth_samples) / len(self.depth_samples)
        
        self.timing_checkpoints.append(("end", self.metrics.end_time))
    
    def record_node_explored(self, depth: int):
        """Record exploration of a search node.
        
        Args:
            depth: Current search depth
        """
        self.metrics.nodes_explored += 1
        self.depth_samples.append(depth)
        self.metrics.max_depth_reached = max(self.metrics.max_depth_reached, depth)
    
    def record_node_pruned(self):
        """Record pruning of a search node."""
        self.metrics.pruned_nodes += 1
    
    def record_cache_hit(self):
        """Record transposition table cache hit."""
        self.metrics.cache_hits += 1
    
    def record_cache_miss(self):
        """Record transposition table cache miss."""
        self.metrics.cache_misses += 1
    
    def record_solution_found(self):
        """Record finding of a solution."""
        self.metrics.solutions_found += 1
        if self.metrics.first_solution_time is None and self._start_time is not None:
            self.metrics.first_solution_time = time.time() - self._start_time
    
    def add_timing_checkpoint(self, name: str):
        """Add a timing checkpoint.
        
        Args:
            name: Name of the checkpoint
        """
        self.timing_checkpoints.append((name, time.time()))
    
    def set_memory_usage(self, peak_memory: int, tt_size: int):
        """Set memory usage metrics.
        
        Args:
            peak_memory: Peak memory usage in bytes
            tt_size: Transposition table size
        """
        self.metrics.peak_memory_usage = peak_memory
        self.metrics.transposition_table_size = tt_size
    
    def add_custom_metric(self, name: str, value: Any):
        """Add a custom metric.
        
        Args:
            name: Metric name
            value: Metric value
        """
        self.metrics.custom_metrics[name] = value
    
    def get_metrics(self) -> SolverMetrics:
        """Get current metrics.
        
        Returns:
            Current metrics object
        """
        return self.metrics
    
    def get_timing_breakdown(self) -> Dict[str, float]:
        """Get timing breakdown between checkpoints.
        
        Returns:
            Dictionary of checkpoint intervals
        """
        breakdown = {}
        for i in range(1, len(self.timing_checkpoints)):
            prev_name, prev_time = self.timing_checkpoints[i-1]
            curr_name, curr_time = self.timing_checkpoints[i]
            interval_name = f"{prev_name}_to_{curr_name}"
            breakdown[interval_name] = curr_time - prev_time
        return breakdown
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary.
        
        Returns:
            Dictionary with key performance indicators
        """
        return {
            'total_time': self.metrics.total_time,
            'nodes_explored': self.metrics.nodes_explored,
            'nodes_per_second': self.metrics.nodes_per_second,
            'max_depth': self.metrics.max_depth_reached,
            'pruning_rate': self.metrics.pruning_rate,
            'cache_hit_rate': self.metrics.cache_hit_rate,
            'solutions_found': self.metrics.solutions_found,
            'first_solution_time': self.metrics.first_solution_time
        }
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = SolverMetrics()
        self.depth_samples.clear()
        self.timing_checkpoints.clear()
        self._start_time = None
