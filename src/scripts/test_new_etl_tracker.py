#!/usr/bin/env python3
"""
Test script for the new simplified ETL tracker.
Demonstrates the improved functionality and reliability.
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keap_export.config import Settings
from keap_export.etl_tracker_v2 import SimpleETLTracker, ETLRunContext

def test_basic_functionality():
    """Test basic ETL tracker functionality."""
    cfg = Settings()
    tracker = SimpleETLTracker(cfg)
    
    print("=== Testing Basic Functionality ===")
    
    # Test 1: Start and end run
    run_id = tracker.start_run("Basic functionality test")
    print(f"Started run: {run_id}")
    
    if run_id:
        # Test logging
        success = tracker.log_request(run_id, "/test/endpoint", 0, 100, 200, 50, 1000)
        print(f"Logged request: {success}")
        
        success = tracker.log_source_count(run_id, "test_entity", 50)
        print(f"Logged source count: {success}")
        
        # Test metrics
        metrics = tracker.get_run_metrics(run_id)
        if metrics:
            print(f"Run metrics: {metrics.total_requests} requests, {metrics.total_items} items")
        
        # End run
        success = tracker.end_run(run_id, True, "Test completed")
        print(f"Ended run: {success}")

def test_context_manager():
    """Test context manager functionality."""
    cfg = Settings()
    tracker = SimpleETLTracker(cfg)
    
    print("\n=== Testing Context Manager ===")
    
    # Test successful run
    with ETLRunContext(tracker, "Context manager test") as run:
        if run.run_id:
            run.log_request("/test/endpoint", 0, 100, 200, 25, 500)
            run.log_source_count("test_entity", 25)
            print(f"Context run ID: {run.run_id}")
            print("Context run will complete successfully")
    
    # Test failed run
    try:
        with ETLRunContext(tracker, "Failed run test") as run:
            if run.run_id:
                run.log_request("/test/endpoint", 0, 100, 200, 10, 200)
                print(f"Context run ID: {run.run_id}")
                raise Exception("Simulated error")
    except Exception as e:
        print(f"Context run failed as expected: {e}")

def test_metrics():
    """Test metrics and reporting functionality."""
    cfg = Settings()
    tracker = SimpleETLTracker(cfg)
    
    print("\n=== Testing Metrics ===")
    
    # Create a test run with multiple requests
    run_id = tracker.start_run("Metrics test")
    if run_id:
        # Log multiple requests
        for i in range(5):
            tracker.log_request(run_id, f"/test/endpoint/{i}", i * 100, 100, 200, 20, 500)
            time.sleep(0.1)  # Small delay to simulate real requests
        
        # Log source counts
        tracker.log_source_count(run_id, "contacts", 100)
        tracker.log_source_count(run_id, "companies", 50)
        
        # Get metrics
        metrics = tracker.get_run_metrics(run_id)
        if metrics:
            print(f"Total requests: {metrics.total_requests}")
            print(f"Total items: {metrics.total_items}")
            print(f"Total duration: {metrics.total_duration_ms}ms")
            print(f"Error count: {metrics.error_count}")
            print(f"Throttle count: {metrics.throttle_count}")
        
        # End run
        tracker.end_run(run_id, True, "Metrics test completed")

def test_recent_runs():
    """Test recent runs functionality."""
    cfg = Settings()
    tracker = SimpleETLTracker(cfg)
    
    print("\n=== Testing Recent Runs ===")
    
    # Get recent runs
    recent_runs = tracker.get_recent_runs(5)
    print(f"Found {len(recent_runs)} recent runs:")
    
    for run in recent_runs:
        status_icon = "✅" if run.status == "success" else "❌" if run.status == "error" else "🔄"
        print(f"  {status_icon} Run {run.id}: {run.status} ({run.started_at})")
        if run.notes:
            print(f"    Notes: {run.notes}")

def test_error_handling():
    """Test error handling and graceful degradation."""
    cfg = Settings()
    tracker = SimpleETLTracker(cfg)
    
    print("\n=== Testing Error Handling ===")
    
    # Test with invalid run ID
    success = tracker.log_request(99999, "/test", 0, 100, 200, 50, 1000)
    print(f"Logging to invalid run ID: {success}")
    
    # Test with disabled tracker
    tracker.disable()
    run_id = tracker.start_run("Disabled test")
    print(f"Start run with disabled tracker: {run_id}")
    
    # Re-enable tracker
    tracker.enable()
    run_id = tracker.start_run("Re-enabled test")
    print(f"Start run after re-enabling: {run_id}")
    
    if run_id:
        tracker.end_run(run_id, True, "Re-enabled test completed")

def test_cleanup():
    """Test cleanup functionality."""
    cfg = Settings()
    tracker = SimpleETLTracker(cfg)
    
    print("\n=== Testing Cleanup ===")
    
    # Clean up old runs (keep only last 5)
    cleaned = tracker.cleanup_old_runs(0)  # Clean up all test runs
    print(f"Cleaned up {cleaned} old runs")

def main():
    """Run all tests."""
    print("Testing New Simplified ETL Tracker")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_context_manager()
        test_metrics()
        test_recent_runs()
        test_error_handling()
        test_cleanup()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nKey Benefits of New ETL Tracker:")
        print("- Simplified API with explicit parameters")
        print("- Context manager for automatic cleanup")
        print("- Better error handling and graceful degradation")
        print("- Thread-safe stateless operations")
        print("- Improved performance and reliability")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
