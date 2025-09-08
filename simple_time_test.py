import time

def test_time_limit_logic():
    """Test the basic time limit logic that should be in DLX engine"""
    print("Testing time limit logic...")
    
    # Simulate the DLX engine time limit check
    time_limit_seconds = 3
    start_time = time.time()
    
    # Simulate some work with time checks
    iteration = 0
    while True:
        iteration += 1
        
        # This is the key check that should be in DLX engine
        if time_limit_seconds and (time.time() - start_time) >= time_limit_seconds:
            elapsed = time.time() - start_time
            print(f"Time limit reached after {elapsed:.2f} seconds at iteration {iteration}")
            break
            
        # Simulate some work
        time.sleep(0.1)
        
        if iteration % 10 == 0:
            elapsed = time.time() - start_time
            print(f"Iteration {iteration}, elapsed: {elapsed:.2f}s")
            
        # Safety check to prevent infinite loop
        if iteration > 100:
            print("ERROR: Safety limit reached - time check failed!")
            break
    
    final_elapsed = time.time() - start_time
    if final_elapsed <= time_limit_seconds + 0.5:  # Allow 0.5s tolerance
        print(f"SUCCESS: Time limit respected ({final_elapsed:.2f}s <= {time_limit_seconds + 0.5}s)")
        return True
    else:
        print(f"FAILURE: Time limit exceeded ({final_elapsed:.2f}s > {time_limit_seconds + 0.5}s)")
        return False

if __name__ == "__main__":
    success = test_time_limit_logic()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
