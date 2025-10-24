#!/usr/bin/env python3
"""
Simulate an interrupted sync to test resume functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keap_export.config import Settings
from keap_export.etl_meta import get_etl_tracker

def simulate_interrupted_sync():
    """Simulate an interrupted sync by creating a failed sync progress."""
    cfg = Settings()
    tracker = get_etl_tracker(cfg)
    
    print("Simulating interrupted sync...")
    
    # Start a test run
    run_id = tracker.start_run("Simulated interrupted sync")
    print(f"Started test run with ID: {run_id}")
    
    # Simulate contacts sync that failed at page 3
    tracker.update_sync_progress("contacts", "running", 0, 0)
    tracker.save_checkpoint("contacts", "page", {
        "last_page": 3,
        "page_limit": 1000,
        "total_records": 3000,
        "last_page_records": 1000
    })
    
    # Simulate tags sync that completed successfully
    tracker.update_sync_progress("tags", "completed", 5, 1880)
    
    # Simulate companies sync that failed
    tracker.update_sync_progress("companies", "failed", 2, 1500, "Network timeout")
    
    # Simulate opportunities sync that is still running
    tracker.update_sync_progress("opportunities", "running", 1, 500)
    
    print("Simulated interrupted sync created")
    print("Entities to resume should be: contacts, companies, opportunities")
    
    # Check entities to resume
    entities_to_resume = tracker.get_entities_to_resume()
    print(f"Entities to resume: {entities_to_resume}")
    
    # Don't end the run - leave it in running state to simulate interruption
    print("Run left in running state to simulate interruption")

if __name__ == "__main__":
    simulate_interrupted_sync()
