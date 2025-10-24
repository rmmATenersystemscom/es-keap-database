"""
Simplified ETL Tracker v2
A clean, reliable implementation focused on core ETL tracking functionality.
"""

from __future__ import annotations
import os
import time
import psycopg2
import psycopg2.extras
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from .config import Settings

# Global ETL enablement flag
ETL_ENABLED = os.getenv("ETL_META", "on").lower() not in {"0", "false", "off"}

@dataclass
class ETLRun:
    """Represents an ETL run with its metadata."""
    id: Optional[int]
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    notes: Optional[str]

@dataclass
class ETLMetrics:
    """ETL metrics for a run."""
    total_requests: int = 0
    total_items: int = 0
    total_duration_ms: int = 0
    error_count: int = 0
    throttle_count: int = 0

class SimpleETLTracker:
    """
    Simplified ETL tracker with clean separation of concerns.
    
    Features:
    - Single responsibility: track ETL runs and metrics
    - Simplified API: fewer methods, clearer purpose
    - Better error handling: graceful degradation
    - Connection management: automatic cleanup
    - Thread safety: stateless operations
    """
    
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.enabled = ETL_ENABLED
    
    def _get_connection(self):
        """Get a fresh database connection."""
        conn = psycopg2.connect(
            host=self.cfg.db_host,
            port=self.cfg.db_port,
            dbname=self.cfg.db_name,
            user=self.cfg.db_user,
            password=self.cfg.db_password
        )
        conn.autocommit = True
        return conn
    
    def start_run(self, notes: str = None) -> Optional[int]:
        """
        Start a new ETL run.
        
        Args:
            notes: Optional notes about the run
            
        Returns:
            Run ID if successful, None if disabled or failed
        """
        if not self.enabled:
            return None
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO keap_meta.etl_run_log (status, notes, started_at) VALUES (%s, %s, %s) RETURNING id',
                    ('running', notes, datetime.now())
                )
                run_id = cur.fetchone()[0]
            conn.close()
            return run_id
        except Exception as e:
            print(f"Warning: Failed to start ETL run: {e}")
            return None
    
    def end_run(self, run_id: int, success: bool, notes: str = None) -> bool:
        """
        End an ETL run.
        
        Args:
            run_id: The run ID to end
            success: Whether the run was successful
            notes: Optional additional notes
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not run_id:
            return False
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                status = 'success' if success else 'error'
                cur.execute(
                    'UPDATE keap_meta.etl_run_log SET status = %s, finished_at = %s, notes = COALESCE(notes, \'\') || %s WHERE id = %s',
                    (status, datetime.now(), f"\n{notes}" if notes else '', run_id)
                )
            conn.close()
            return True
        except Exception as e:
            print(f"Warning: Failed to end ETL run {run_id}: {e}")
            return False
    
    def log_request(self, run_id: int, endpoint: str, page_offset: int, 
                   page_limit: int, http_status: int, item_count: int, 
                   duration_ms: int, throttled: bool = False, error: str = None) -> bool:
        """
        Log a request to the ETL run.
        
        Args:
            run_id: The run ID
            endpoint: API endpoint
            page_offset: Page offset
            page_limit: Page limit
            http_status: HTTP status code
            item_count: Number of items returned
            duration_ms: Request duration in milliseconds
            throttled: Whether request was throttled
            error: Error message if any
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not run_id:
            return False
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    '''INSERT INTO keap_meta.etl_request_log 
                       (run_id, endpoint, page_offset, page_limit, http_status, item_count, duration_ms, throttled, error) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (run_id, endpoint, page_offset, page_limit, http_status, item_count, duration_ms, throttled, error)
                )
            conn.close()
            return True
        except Exception as e:
            print(f"Warning: Failed to log request for run {run_id}: {e}")
            return False
    
    def log_source_count(self, run_id: int, entity: str, count: int) -> bool:
        """
        Log source count for an entity.
        
        Args:
            run_id: The run ID
            entity: Entity name
            count: Number of items processed
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not run_id:
            return False
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    '''INSERT INTO keap_meta.source_counts (run_id, entity, items_retrieved) 
                       VALUES (%s, %s, %s) 
                       ON CONFLICT (run_id, entity) 
                       DO UPDATE SET items_retrieved = EXCLUDED.items_retrieved''',
                    (run_id, entity, count)
                )
            conn.close()
            return True
        except Exception as e:
            print(f"Warning: Failed to log source count for run {run_id}, entity {entity}: {e}")
            return False
    
    def get_run_metrics(self, run_id: int) -> Optional[ETLMetrics]:
        """
        Get metrics for a specific run.
        
        Args:
            run_id: The run ID
            
        Returns:
            ETLMetrics object or None if not found
        """
        if not self.enabled or not run_id:
            return None
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    '''SELECT 
                        COUNT(*) as total_requests,
                        SUM(item_count) as total_items,
                        SUM(duration_ms) as total_duration_ms,
                        COUNT(CASE WHEN error IS NOT NULL THEN 1 END) as error_count,
                        COUNT(CASE WHEN throttled = true THEN 1 END) as throttle_count
                       FROM keap_meta.etl_request_log 
                       WHERE run_id = %s''',
                    (run_id,)
                )
                result = cur.fetchone()
                conn.close()
                
                if result:
                    return ETLMetrics(
                        total_requests=result[0] or 0,
                        total_items=result[1] or 0,
                        total_duration_ms=result[2] or 0,
                        error_count=result[3] or 0,
                        throttle_count=result[4] or 0
                    )
                return None
        except Exception as e:
            print(f"Warning: Failed to get metrics for run {run_id}: {e}")
            return None
    
    def get_recent_runs(self, limit: int = 10) -> List[ETLRun]:
        """
        Get recent ETL runs.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of ETLRun objects
        """
        if not self.enabled:
            return []
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    '''SELECT id, status, started_at, finished_at, notes 
                       FROM keap_meta.etl_run_log 
                       ORDER BY started_at DESC 
                       LIMIT %s''',
                    (limit,)
                )
                runs = []
                for row in cur.fetchall():
                    runs.append(ETLRun(
                        id=row[0],
                        status=row[1],
                        started_at=row[2],
                        finished_at=row[3],
                        notes=row[4]
                    ))
                conn.close()
                return runs
        except Exception as e:
            print(f"Warning: Failed to get recent runs: {e}")
            return []
    
    def cleanup_old_runs(self, days: int = 30) -> int:
        """
        Clean up old ETL runs and their associated data.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of runs cleaned up
        """
        if not self.enabled:
            return 0
        
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Get count before deletion
                cur.execute(
                    '''SELECT COUNT(*) FROM keap_meta.etl_run_log 
                       WHERE started_at < NOW() - INTERVAL '%s days' ''',
                    (days,)
                )
                count = cur.fetchone()[0]
                
                # Delete old runs (cascade will handle related data)
                cur.execute(
                    '''DELETE FROM keap_meta.etl_run_log 
                       WHERE started_at < NOW() - INTERVAL '%s days' ''',
                    (days,)
                )
                conn.close()
                return count
        except Exception as e:
            print(f"Warning: Failed to cleanup old runs: {e}")
            return 0
    
    def is_enabled(self) -> bool:
        """Check if ETL tracking is enabled."""
        return self.enabled
    
    def disable(self):
        """Disable ETL tracking."""
        self.enabled = False
    
    def enable(self):
        """Enable ETL tracking."""
        self.enabled = ETL_ENABLED

# Factory function for backward compatibility
def get_etl_tracker(cfg: Settings) -> SimpleETLTracker:
    """Get a new ETL tracker instance."""
    return SimpleETLTracker(cfg)

# Context manager for automatic run management
class ETLRunContext:
    """Context manager for ETL runs with automatic cleanup."""
    
    def __init__(self, tracker: SimpleETLTracker, notes: str = None):
        self.tracker = tracker
        self.notes = notes
        self.run_id = None
        self.success = False
    
    def __enter__(self):
        self.run_id = self.tracker.start_run(self.notes)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.run_id:
            self.success = exc_type is None
            self.tracker.end_run(self.run_id, self.success, 
                               str(exc_val) if exc_val else None)
    
    def log_request(self, endpoint: str, page_offset: int, page_limit: int,
                   http_status: int, item_count: int, duration_ms: int,
                   throttled: bool = False, error: str = None):
        """Log a request to this run."""
        if self.run_id:
            self.tracker.log_request(self.run_id, endpoint, page_offset, page_limit,
                                   http_status, item_count, duration_ms, throttled, error)
    
    def log_source_count(self, entity: str, count: int):
        """Log source count for this run."""
        if self.run_id:
            self.tracker.log_source_count(self.run_id, entity, count)
