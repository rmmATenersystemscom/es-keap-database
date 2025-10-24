#!/usr/bin/env python3
"""
Test script for observability metrics.
This script demonstrates the comprehensive monitoring capabilities.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keap_export.config import Settings
from keap_export.etl_meta import get_etl_tracker

def test_observability_metrics():
    """Test the observability metrics functionality."""
    cfg = Settings()
    tracker = get_etl_tracker(cfg)
    
    print("Testing observability metrics...")
    
    # Start a test run
    run_id = tracker.start_run("Observability metrics test")
    print(f"Started test run with ID: {run_id}")
    
    # Simulate detailed request metrics
    tracker.log_detailed_request(
        entity="contacts",
        endpoint="/crm/rest/v1/contacts",
        page_offset=0,
        page_limit=1000,
        http_status=200,
        item_count=1000,
        duration_ms=850,
        throttle_remaining=95,
        throttle_type="api",
        retry_count=0,
        response_size_bytes=2048576
    )
    
    # Simulate throttle events
    tracker.log_throttle_event(
        entity="contacts",
        endpoint="/crm/rest/v1/contacts",
        throttle_type="api",
        throttle_remaining=5,
        wait_time_ms=2000
    )
    
    # Simulate error events
    tracker.log_error_event(
        entity="contacts",
        endpoint="/crm/rest/v1/contacts",
        error_type="timeout",
        error_message="Request timeout after 60 seconds",
        error_context={"retry_count": 3, "last_error": "Connection timeout"},
        retry_count=3
    )
    
    # Simulate system health metrics
    tracker.log_system_health(
        metric_name="memory_usage",
        metric_value=512.5,
        metric_unit="MB",
        tags={"component": "sync", "entity": "contacts"}
    )
    
    tracker.log_system_health(
        metric_name="cpu_usage",
        metric_value=75.2,
        metric_unit="percent",
        tags={"component": "sync", "entity": "contacts"}
    )
    
    # Calculate performance metrics
    tracker.calculate_entity_performance("contacts")
    
    print("Observability metrics test completed")
    
    # End the run
    tracker.end_run(success=True, notes="Observability test completed")

if __name__ == "__main__":
    test_observability_metrics()
