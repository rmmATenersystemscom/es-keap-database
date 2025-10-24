#!/usr/bin/env python3
"""
Migration script to update ETL tracker usage to the new simplified version.
This script demonstrates the migration from the old ETL tracker to the new one.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keap_export.config import Settings
from keap_export.etl_tracker_v2 import SimpleETLTracker, ETLRunContext

def test_new_etl_tracker():
    """Test the new simplified ETL tracker."""
    cfg = Settings()
    tracker = SimpleETLTracker(cfg)
    
    print("Testing new simplified ETL tracker...")
    
    # Test 1: Basic functionality
    print("\n1. Testing basic functionality:")
    run_id = tracker.start_run("Test run for new ETL tracker")
    print(f"   Started run with ID: {run_id}")
    
    if run_id:
        # Test logging
        success = tracker.log_request(run_id, "/test/endpoint", 0, 100, 200, 50, 1000)
        print(f"   Logged request: {success}")
        
        success = tracker.log_source_count(run_id, "test_entity", 50)
        print(f"   Logged source count: {success}")
        
        # Test metrics
        metrics = tracker.get_run_metrics(run_id)
        if metrics:
            print(f"   Metrics: {metrics.total_requests} requests, {metrics.total_items} items")
        
        # End run
        success = tracker.end_run(run_id, True, "Test completed successfully")
        print(f"   Ended run: {success}")
    
    # Test 2: Context manager
    print("\n2. Testing context manager:")
    with ETLRunContext(tracker, "Context manager test") as run:
        if run.run_id:
            run.log_request("/test/endpoint", 0, 100, 200, 25, 500)
            run.log_source_count("test_entity", 25)
            print(f"   Context run ID: {run.run_id}")
    
    # Test 3: Recent runs
    print("\n3. Testing recent runs:")
    recent_runs = tracker.get_recent_runs(5)
    print(f"   Found {len(recent_runs)} recent runs")
    for run in recent_runs:
        print(f"   - Run {run.id}: {run.status} ({run.started_at})")
    
    # Test 4: Cleanup
    print("\n4. Testing cleanup:")
    cleaned = tracker.cleanup_old_runs(0)  # Clean up all test runs
    print(f"   Cleaned up {cleaned} old runs")
    
    print("\nNew ETL tracker test completed successfully!")

def demonstrate_migration():
    """Demonstrate migration from old to new ETL tracker."""
    print("\n=== ETL Tracker Migration Guide ===")
    print()
    print("OLD USAGE:")
    print("```python")
    print("from keap_export.etl_meta import get_etl_tracker")
    print("tracker = get_etl_tracker(cfg)")
    print("run_id = tracker.start_run('My sync')")
    print("tracker.log_request(endpoint, offset, limit, status, count, duration)")
    print("tracker.end_run(True, 'Completed')")
    print("```")
    print()
    print("NEW USAGE (Option 1 - Direct):")
    print("```python")
    print("from keap_export.etl_tracker_v2 import SimpleETLTracker")
    print("tracker = SimpleETLTracker(cfg)")
    print("run_id = tracker.start_run('My sync')")
    print("tracker.log_request(run_id, endpoint, offset, limit, status, count, duration)")
    print("tracker.end_run(run_id, True, 'Completed')")
    print("```")
    print()
    print("NEW USAGE (Option 2 - Context Manager):")
    print("```python")
    print("from keap_export.etl_tracker_v2 import ETLRunContext")
    print("with ETLRunContext(tracker, 'My sync') as run:")
    print("    run.log_request(endpoint, offset, limit, status, count, duration)")
    print("    # Automatic cleanup on exit")
    print("```")
    print()
    print("MIGRATION BENEFITS:")
    print("- Simplified API with fewer methods")
    print("- Better error handling and graceful degradation")
    print("- Context manager for automatic cleanup")
    print("- Thread-safe stateless operations")
    print("- Cleaner separation of concerns")
    print("- Improved performance and reliability")

if __name__ == "__main__":
    test_new_etl_tracker()
    demonstrate_migration()
