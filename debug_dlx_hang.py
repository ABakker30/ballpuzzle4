import time
import sys
import os

def test_dlx_entry_point():
    """Test where exactly the DLX engine hangs"""
    print("Testing DLX engine entry point...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(__file__))
        
        print("1. Importing DLX engine...")
        from src.solver.engines.dlx_engine import DLXEngine
        print("   OK Import successful")
        
        print("2. Creating engine instance...")
        engine = DLXEngine()
        print("   OK Engine created")
        
        print("3. Preparing test data...")
        container_data = {
            "coordinates": [
                [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]  # Just 4 cells
            ]
        }
        inventory = {"A": 1}  # Just one piece
        print("   OK Test data prepared")
        
        print("4. Starting solve() with 2-second timeout...")
        start_time = time.time()
        
        # Try to get just the first event from the generator
        solve_gen = engine.solve(
            container=container_data["coordinates"],
            inventory={"pieces": inventory},
            pieces=None,
            options={"max_results": 1, "seed": 42, "time_limit_seconds": 2}
        )
        
        print("5. Getting first event from generator...")
        try:
            first_event = next(solve_gen)
            elapsed = time.time() - start_time
            print(f"   OK Got first event after {elapsed:.2f}s: {type(first_event)}")
        except StopIteration:
            elapsed = time.time() - start_time
            print(f"   OK Generator completed after {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ERROR Exception after {elapsed:.2f}s: {e}")
            
        total_elapsed = time.time() - start_time
        print(f"6. Total test time: {total_elapsed:.2f}s")
        
        if total_elapsed <= 3.0:
            print("SUCCESS: DLX engine responded within timeout")
            return True
        else:
            print(f"FAILURE: DLX engine took {total_elapsed:.2f}s (> 3.0s)")
            return False
            
    except ImportError as e:
        print(f"   ERROR Import failed: {e}")
        return False
    except Exception as e:
        elapsed = time.time() - start_time if 'start_time' in locals() else 0
        print(f"   ERROR Unexpected error after {elapsed:.2f}s: {e}")
        return False

if __name__ == "__main__":
    success = test_dlx_entry_point()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")
