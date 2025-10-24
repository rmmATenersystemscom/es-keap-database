#!/usr/bin/env python3
"""
Test script for resume functionality.
This script demonstrates how to use the resume capability.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keap_export.config import Settings
from keap_export.etl_meta import get_etl_tracker

def test_resume_functionality():
    """Test the resume functionality."""
    cfg = Settings()
    tracker = get_etl_tracker(cfg)
    
    print("Testing resume functionality...")
    
    # Start a test run
    run_id = tracker.start_run("Test resume functionality")
    print(f"Started test run with ID: {run_id}")
    
    # Simulate some sync progress
    tracker.update_sync_progress("contacts", "running", 0, 0)
    tracker.save_checkpoint("contacts", "page", {
        "last_page": 2,
        "page_limit": 1000,
        "total_records": 2000,
        "last_page_records": 1000
    })
    
    # Check entities to resume
    entities_to_resume = tracker.get_entities_to_resume()
    print(f"Entities to resume: {entities_to_resume}")
    
    # Get checkpoint data
    checkpoint = tracker.get_last_checkpoint("contacts", "page")
    print(f"Last checkpoint for contacts: {checkpoint}")
    
    # Mark as completed
    tracker.update_sync_progress("contacts", "completed", 5, 5000)
    
    # End the run
    tracker.end_run(success=True, notes="Test completed")
    print("Test run completed successfully")

if __name__ == "__main__":
    test_resume_functionality()
