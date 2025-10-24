from __future__ import annotations
import os
import psycopg2
import psycopg2.extras
from dataclasses import dataclass
from typing import Optional
from .config import Settings

ETL_ENABLED = os.getenv("ETL_META", "on").lower() not in {"0", "false", "off"}

@dataclass
class EtlRun:
    run_id: Optional[int]
    enabled: bool

class EtlTracker:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self._conn = None
        self.run_id = None
        self.enabled = ETL_ENABLED

    def _conn_autocommit(self):
        if self._conn is None:
            self._conn = psycopg2.connect(
                host=self.cfg.db_host, port=self.cfg.db_port,
                dbname=self.cfg.db_name, user=self.cfg.db_user, password=self.cfg.db_password
            )
            self._conn.autocommit = True  # critical: don't depend on caller tx
        return self._conn

    def start_run(self, notes: str = None) -> int:
        if not self.enabled:
            return None
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute('insert into keap_meta.etl_run_log(status, notes) values (%s, %s) returning id', ('running', notes))
            self.run_id = cur.fetchone()[0]
        return self.run_id

    def log_request(self, endpoint: str, page_offset: int, page_limit: int, http_status: int, item_count: int, duration_ms: int, throttled: bool = False, error: str = None):
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                'insert into keap_meta.etl_request_log (run_id, endpoint, page_offset, page_limit, http_status, item_count, duration_ms, throttled, error) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (self.run_id, endpoint, page_offset, page_limit, http_status, item_count, duration_ms, throttled, error)
            )
    
    def log_detailed_request(self, entity: str, endpoint: str, page_offset: int = None, 
                           page_limit: int = None, http_status: int = None, item_count: int = None,
                           duration_ms: int = None, throttle_remaining: int = None,
                           throttle_reset_time: str = None, throttle_type: str = None,
                           retry_count: int = 0, error_message: str = None,
                           response_size_bytes: int = None):
        """Log detailed request metrics."""
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                '''insert into keap_meta.etl_request_metrics 
                   (run_id, entity, endpoint, page_offset, page_limit, http_status, item_count, 
                    duration_ms, throttle_remaining, throttle_reset_time, throttle_type, 
                    retry_count, error_message, response_size_bytes) 
                   values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (self.run_id, entity, endpoint, page_offset, page_limit, http_status, item_count,
                 duration_ms, throttle_remaining, throttle_reset_time, throttle_type,
                 retry_count, error_message, response_size_bytes)
            )
    
    def log_throttle_event(self, entity: str, endpoint: str, throttle_type: str,
                          throttle_remaining: int, throttle_reset_time: str = None,
                          wait_time_ms: int = None):
        """Log a throttle event."""
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                '''insert into keap_meta.throttle_events 
                   (run_id, entity, endpoint, throttle_type, throttle_remaining, 
                    throttle_reset_time, wait_time_ms) 
                   values (%s, %s, %s, %s, %s, %s, %s)''',
                (self.run_id, entity, endpoint, throttle_type, throttle_remaining,
                 throttle_reset_time, wait_time_ms)
            )
    
    def log_error_event(self, entity: str, endpoint: str, error_type: str, error_message: str,
                       error_context: dict = None, retry_count: int = 0):
        """Log an error event."""
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                '''insert into keap_meta.error_events 
                   (run_id, entity, endpoint, error_type, error_message, error_context, retry_count) 
                   values (%s, %s, %s, %s, %s, %s, %s)''',
                (self.run_id, entity, endpoint, error_type, error_message, 
                 psycopg2.extras.Json(error_context or {}), retry_count)
            )
    
    def log_system_health(self, metric_name: str, metric_value: float, metric_unit: str = None,
                         tags: dict = None):
        """Log system health metrics."""
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                '''insert into keap_meta.system_health 
                   (run_id, metric_name, metric_value, metric_unit, tags) 
                   values (%s, %s, %s, %s, %s)''',
                (self.run_id, metric_name, metric_value, metric_unit, 
                 psycopg2.extras.Json(tags or {}))
            )
    
    def calculate_entity_performance(self, entity: str):
        """Calculate and store performance metrics for an entity."""
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                'select keap_meta.calculate_entity_performance(%s, %s)',
                (self.run_id, entity)
            )

    def end_run(self, success: bool, notes: str = None):
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                'update keap_meta.etl_run_log set status=%s, finished_at=now(), notes=coalesce(notes,\'\') || %s where id=%s',
                ('success' if success else 'error', f"\n{notes}" if notes else '', self.run_id)
            )
        self._conn.close()
        self._conn = None
        self.run_id = None

    def finish_run(self, status: str, notes: str = None):
        """Alias for end_run for backward compatibility."""
        self.end_run(status == 'success', notes)

    def get_run_summary(self) -> dict:
        """Get summary of the current run."""
        if not self.enabled or self.run_id is None:
            return {"enabled": False}
        return {
            "enabled": True,
            "run_id": self.run_id,
            "status": "running" if self.run_id else "not_started"
        }

    def record_source_count(self, entity: str, count: int):
        """Record source count for an entity."""
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                'insert into keap_meta.source_counts (run_id, entity, items_retrieved) values (%s, %s, %s) on conflict (run_id, entity) do update set items_retrieved = excluded.items_retrieved',
                (self.run_id, entity, count)
            )
    
    def update_sync_progress(self, entity: str, status: str, page_offset: int = None, 
                           items_processed: int = None, error_msg: str = None):
        """Update sync progress for an entity."""
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                'select keap_meta.update_sync_progress(%s, %s, %s, %s, %s, %s)',
                (self.run_id, entity, status, page_offset, items_processed, error_msg)
            )
    
    def save_checkpoint(self, entity: str, checkpoint_type: str, checkpoint_data: dict):
        """Save a checkpoint for an entity."""
        if not self.enabled or self.run_id is None:
            return
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                'select keap_meta.save_checkpoint(%s, %s, %s, %s)',
                (self.run_id, entity, checkpoint_type, psycopg2.extras.Json(checkpoint_data))
            )
    
    def get_last_checkpoint(self, entity: str, checkpoint_type: str) -> dict:
        """Get the last checkpoint for an entity."""
        if not self.enabled or self.run_id is None:
            return {}
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                'select keap_meta.get_last_checkpoint(%s, %s, %s)',
                (self.run_id, entity, checkpoint_type)
            )
            result = cur.fetchone()
            return result[0] if result and result[0] else {}
    
    def get_entities_to_resume(self) -> list:
        """Get entities that need to be resumed."""
        if not self.enabled or self.run_id is None:
            return []
        conn = self._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute(
                'select * from keap_meta.get_entities_to_resume(%s)',
                (self.run_id,)
            )
            return [row[0] for row in cur.fetchall()]

def get_etl_tracker(cfg: Settings) -> EtlTracker:
    """Get ETL tracker instance."""
    return EtlTracker(cfg)