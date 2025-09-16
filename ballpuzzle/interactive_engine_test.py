#!/usr/bin/env python3
"""Interactive engine test script with progress reporting and user control."""

import sys
import time
import threading
import signal
from typing import Optional, Dict, Any
from src.solver.engines.engine_c.api_adapter import EngineCAdapter
from src.solver.engines.dfs_engine import DFSEngine
from src.solver.engines.dlx_engine import DLXEngine
from src.io.container import load_container
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y

class InteractiveEngineTest:
    def __init__(self):
        self.stop_requested = False
        self.current_engine = None
        self.start_time = None
        self.last_progress = None
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n*** Stop requested by user (Ctrl+C) ***")
        self.stop_requested = True
        
    def setup_signal_handling(self):
        """Setup signal handling for graceful interruption."""
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def get_user_input_async(self):
        """Get user input in separate thread to allow interruption."""
        def input_thread():
            try:
                while not self.stop_requested:
                    user_input = input().strip().lower()
                    if user_input in ['q', 'quit', 'stop', 's']:
                        self.stop_requested = True
                        break
                    time.sleep(0.1)
            except:
                pass
        
        thread = threading.Thread(target=input_thread, daemon=True)
        thread.start()
        
    def test_engine(self, engine_name: str, container_path: str, inventory: Dict, 
                   time_budget: float = 60.0, progress_interval: int = 2000):
        """Test an engine with progress reporting and user control."""
        
        print(f"\n=== Testing {engine_name.upper()} Engine ===")
        
        # Load container and pieces
        container = load_container(container_path)
        pieces = load_fcc_A_to_Y()
        
        print(f"Container: {len(container['coordinates'])} cells")
        print(f"Inventory: {sum(inventory['pieces'].values())} pieces")
        print("Press 'q', 'quit', 'stop', or 's' + Enter to stop, or Ctrl+C")
        
        # Select engine
        engines = {
            'engine-c': EngineCAdapter(),
            'dfs': DFSEngine(), 
            'dlx': DLXEngine()
        }
        
        if engine_name not in engines:
            print(f"Unknown engine: {engine_name}")
            return
            
        engine = engines[engine_name]
        self.current_engine = engine
        
        # Setup options
        options = {
            'seed': 20250907,
            'max_results': 1,
            'progress_interval_ms': progress_interval,
            'flags': {
                'time_budget_s': time_budget,
                'pruning_level': 'basic',
                'shuffle': 'ties_only'
            }
        }
        
        # Start async input monitoring
        self.get_user_input_async()
        
        # Run engine
        self.start_time = time.time()
        solutions_found = 0
        max_depth = 0
        nodes_explored = 0
        progress_count = 0
        
        try:
            for event in engine.solve(container, inventory, pieces, options):
                if self.stop_requested:
                    print("*** Stopping engine ***")
                    break
                    
                if event['type'] == 'tick':
                    progress_count += 1
                    metrics = event['metrics']
                    elapsed = time.time() - self.start_time
                    
                    # Update tracking
                    nodes_explored = metrics.get('nodes', 0)
                    depth = metrics.get('depth', 0)
                    max_depth = max(max_depth, depth)
                    
                    # Progress display
                    print(f"[{elapsed:6.1f}s] Nodes: {nodes_explored:6d} | "
                          f"Depth: {depth:2d} | "
                          f"Pruned: {metrics.get('pruned', 0):6d} | "
                          f"Solutions: {solutions_found}")
                    
                    self.last_progress = {
                        'elapsed': elapsed,
                        'nodes': nodes_explored,
                        'depth': depth,
                        'max_depth': max_depth
                    }
                    
                elif event['type'] == 'solution':
                    solutions_found += 1
                    solution = event['solution']
                    placements = solution.get('placements', [])
                    
                    print(f"\n*** SOLUTION #{solutions_found} FOUND! ***")
                    print(f"Pieces placed: {len(placements)}")
                    print(f"Cells covered: {len(placements) * 4}")
                    
                    # Show piece usage
                    pieces_used = {}
                    for placement in placements:
                        piece_id = placement['piece']
                        pieces_used[piece_id] = pieces_used.get(piece_id, 0) + 1
                    
                    if pieces_used:
                        usage_str = ', '.join([f'{k}={v}' for k, v in sorted(pieces_used.items())])
                        print(f"Pieces used: {usage_str}")
                    
                elif event['type'] == 'done':
                    elapsed = time.time() - self.start_time
                    metrics = event['metrics']
                    
                    print(f"\n=== {engine_name.upper()} COMPLETED ===")
                    print(f"Time: {elapsed:.2f}s")
                    print(f"Solutions: {metrics.get('solutions', 0)}")
                    print(f"Nodes explored: {metrics.get('nodes', 0)}")
                    print(f"Nodes pruned: {metrics.get('pruned', 0)}")
                    print(f"Max depth: {metrics.get('bestDepth', max_depth)}")
                    print(f"Progress updates: {progress_count}")
                    
                    if metrics.get('solutions', 0) > 0:
                        print("*** COMPLETE SOLUTION FOUND! ***")
                    else:
                        depth_reached = metrics.get('bestDepth', max_depth)
                        print(f"No complete solution. Reached depth {depth_reached} ({depth_reached} pieces placed)")
                    
                    break
                    
        except KeyboardInterrupt:
            elapsed = time.time() - self.start_time if self.start_time else 0
            print(f"\n*** INTERRUPTED after {elapsed:.1f}s ***")
            if self.last_progress:
                print(f"Final state: {self.last_progress['nodes']} nodes, depth {self.last_progress['max_depth']}")
        
        except Exception as e:
            print(f"\n*** ERROR: {e} ***")
            
        finally:
            self.stop_requested = True
            self.current_engine = None

def main():
    """Main interactive test interface."""
    tester = InteractiveEngineTest()
    tester.setup_signal_handling()
    
    print("=== Interactive Engine Test Suite ===")
    print("Tests engines with progress reporting and user control")
    
    # Test configurations
    tests = [
        {
            'name': 'Quick Engine-C Test',
            'engine': 'engine-c',
            'container': 'data/containers/legacy_fixed/Shape_3.json',
            'inventory': {'pieces': {p: 1 for p in 'ABCDE'}},  # 5 pieces
            'time_budget': 30.0,
            'progress_interval': 1000
        },
        {
            'name': 'Medium Engine-C Test', 
            'engine': 'engine-c',
            'container': 'data/containers/legacy_fixed/Shape_3.json',
            'inventory': {'pieces': {p: 2 for p in 'ABCDEFGHIJ'}},  # 20 pieces
            'time_budget': 60.0,
            'progress_interval': 2000
        },
        {
            'name': 'DFS Comparison',
            'engine': 'dfs',
            'container': 'data/containers/legacy_fixed/Shape_3.json', 
            'inventory': {'pieces': {p: 1 for p in 'ABCDE'}},  # 5 pieces
            'time_budget': 30.0,
            'progress_interval': 1000
        }
    ]
    
    while True:
        print(f"\nAvailable tests:")
        for i, test in enumerate(tests, 1):
            print(f"{i}. {test['name']} ({test['engine']}, {sum(test['inventory']['pieces'].values())} pieces, {test['time_budget']}s)")
        print("q. Quit")
        
        choice = input("\nSelect test (1-3) or 'q' to quit: ").strip()
        
        if choice.lower() in ['q', 'quit']:
            break
            
        try:
            test_idx = int(choice) - 1
            if 0 <= test_idx < len(tests):
                test = tests[test_idx]
                tester.test_engine(
                    test['engine'],
                    test['container'], 
                    test['inventory'],
                    test['time_budget'],
                    test['progress_interval']
                )
                tester.stop_requested = False  # Reset for next test
            else:
                print("Invalid choice")
        except ValueError:
            print("Invalid choice")
    
    print("Goodbye!")

if __name__ == '__main__':
    main()
