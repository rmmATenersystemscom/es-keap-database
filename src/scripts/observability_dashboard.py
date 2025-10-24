#!/usr/bin/env python3
"""
Observability Dashboard
This script provides comprehensive monitoring and analytics for the Keap sync process.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
from keap_export.config import Settings

def get_connection():
    """Get database connection."""
    cfg = Settings()
    return psycopg2.connect(
        host=cfg.db_host, port=cfg.db_port,
        dbname=cfg.db_name, user=cfg.db_user, password=cfg.db_password
    )

def show_run_summary():
    """Show summary of recent runs."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                rl.id,
                rl.started_at,
                rl.finished_at,
                rl.status,
                rl.notes,
                EXTRACT(EPOCH FROM (rl.finished_at - rl.started_at)) as duration_seconds
            FROM keap_meta.etl_run_log rl
            ORDER BY rl.started_at DESC
            LIMIT 10
        """)
        
        print("=== Recent ETL Runs ===")
        print(f"{'ID':<4} {'Started':<20} {'Duration':<10} {'Status':<10} {'Notes'}")
        print("-" * 80)
        
        for row in cur.fetchall():
            run_id, started_at, finished_at, status, notes, duration = row
            duration_str = f"{duration:.1f}s" if duration else "N/A"
            started_str = started_at.strftime("%Y-%m-%d %H:%M:%S") if started_at else "N/A"
            print(f"{run_id:<4} {started_str:<20} {duration_str:<10} {status:<10} {notes or ''}")

def show_performance_metrics(run_id=None):
    """Show performance metrics for a specific run or latest run."""
    conn = get_connection()
    with conn.cursor() as cur:
        if run_id is None:
            # Get latest run
            cur.execute("SELECT id FROM keap_meta.etl_run_log ORDER BY started_at DESC LIMIT 1")
            result = cur.fetchone()
            if not result:
                print("No runs found")
                return
            run_id = result[0]
        
        cur.execute("""
            SELECT * FROM keap_meta.get_run_performance_summary(%s)
        """, (run_id,))
        
        print(f"\n=== Performance Metrics for Run {run_id} ===")
        print(f"{'Entity':<12} {'Pages':<6} {'Items':<8} {'Duration':<10} {'Avg Page':<10} {'Throttle':<8} {'Errors':<6} {'Throughput':<12}")
        print("-" * 90)
        
        for row in cur.fetchall():
            entity, pages, items, duration, avg_page, throttle, errors, throughput = row
            duration_str = f"{duration}ms" if duration else "N/A"
            avg_page_str = f"{avg_page:.1f}ms" if avg_page else "N/A"
            throughput_str = f"{throughput:.1f}/s" if throughput else "N/A"
            print(f"{entity:<12} {pages:<6} {items:<8} {duration_str:<10} {avg_page_str:<10} {throttle:<8} {errors:<6} {throughput_str:<12}")

def show_throttle_analysis(run_id=None):
    """Show throttle analysis for a specific run or latest run."""
    conn = get_connection()
    with conn.cursor() as cur:
        if run_id is None:
            # Get latest run
            cur.execute("SELECT id FROM keap_meta.etl_run_log ORDER BY started_at DESC LIMIT 1")
            result = cur.fetchone()
            if not result:
                print("No runs found")
                return
            run_id = result[0]
        
        cur.execute("""
            SELECT * FROM keap_meta.get_throttle_analysis(%s)
        """, (run_id,))
        
        print(f"\n=== Throttle Analysis for Run {run_id} ===")
        print(f"{'Entity':<12} {'Endpoint':<25} {'Type':<12} {'Events':<8} {'Avg Remaining':<15} {'Total Wait':<12}")
        print("-" * 90)
        
        for row in cur.fetchall():
            entity, endpoint, throttle_type, events, avg_remaining, total_wait = row
            avg_remaining_str = f"{avg_remaining:.1f}" if avg_remaining else "N/A"
            total_wait_str = f"{total_wait}ms" if total_wait else "N/A"
            print(f"{entity:<12} {endpoint:<25} {throttle_type:<12} {events:<8} {avg_remaining_str:<15} {total_wait_str:<12}")

def show_error_analysis(run_id=None):
    """Show error analysis for a specific run or latest run."""
    conn = get_connection()
    with conn.cursor() as cur:
        if run_id is None:
            # Get latest run
            cur.execute("SELECT id FROM keap_meta.etl_run_log ORDER BY started_at DESC LIMIT 1")
            result = cur.fetchone()
            if not result:
                print("No runs found")
                return
            run_id = result[0]
        
        cur.execute("""
            SELECT * FROM keap_meta.get_error_analysis(%s)
        """, (run_id,))
        
        print(f"\n=== Error Analysis for Run {run_id} ===")
        print(f"{'Entity':<12} {'Error Type':<15} {'Count':<6} {'Sample Message'}")
        print("-" * 80)
        
        for row in cur.fetchall():
            entity, error_type, count, sample = row
            sample_str = (sample[:50] + "...") if sample and len(sample) > 50 else (sample or "")
            print(f"{entity:<12} {error_type:<15} {count:<6} {sample_str}")

def show_system_health(run_id=None):
    """Show system health metrics for a specific run or latest run."""
    conn = get_connection()
    with conn.cursor() as cur:
        if run_id is None:
            # Get latest run
            cur.execute("SELECT id FROM keap_meta.etl_run_log ORDER BY started_at DESC LIMIT 1")
            result = cur.fetchone()
            if not result:
                print("No runs found")
                return
            run_id = result[0]
        
        cur.execute("""
            SELECT 
                metric_name,
                metric_value,
                metric_unit,
                tags,
                recorded_at
            FROM keap_meta.system_health
            WHERE run_id = %s
            ORDER BY recorded_at DESC
        """, (run_id,))
        
        print(f"\n=== System Health Metrics for Run {run_id} ===")
        print(f"{'Metric':<20} {'Value':<10} {'Unit':<10} {'Tags':<30} {'Recorded'}")
        print("-" * 90)
        
        for row in cur.fetchall():
            metric_name, value, unit, tags, recorded_at = row
            tags_str = str(tags)[:30] if tags else ""
            recorded_str = recorded_at.strftime("%H:%M:%S") if recorded_at else "N/A"
            print(f"{metric_name:<20} {value:<10} {unit or '':<10} {tags_str:<30} {recorded_str}")

def main():
    """Main dashboard function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Keap Sync Observability Dashboard")
    parser.add_argument("--run-id", type=int, help="Specific run ID to analyze")
    parser.add_argument("--sections", nargs="+", 
                       choices=["summary", "performance", "throttle", "errors", "health"],
                       default=["summary", "performance", "throttle", "errors", "health"],
                       help="Sections to display")
    
    args = parser.parse_args()
    
    try:
        if "summary" in args.sections:
            show_run_summary()
        
        if "performance" in args.sections:
            show_performance_metrics(args.run_id)
        
        if "throttle" in args.sections:
            show_throttle_analysis(args.run_id)
        
        if "errors" in args.sections:
            show_error_analysis(args.run_id)
        
        if "health" in args.sections:
            show_system_health(args.run_id)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
