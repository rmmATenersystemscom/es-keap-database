from __future__ import annotations
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from .config import Settings
from .db import get_conn

class ETLMetadataTracker:
    """Track ETL run metadata, request logs, and source counts."""
    
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.run_id: Optional[int] = None
        self.start_time: Optional[datetime] = None
    
    def start_run(self, notes: Optional[str] = None) -> int:
        """Start a new ETL run and return the run ID."""
        conn = get_conn(self.cfg)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into keap_meta.etl_run_log (started_at, status, notes)
                    values (now(), 'running', %s)
                    returning id
                    """,
                    (notes,)
                )
                self.run_id = cur.fetchone()[0]
                conn.commit()
                self.start_time = datetime.utcnow()
                return self.run_id
        finally:
            conn.close()
    
    def finish_run(self, status: str = 'success', notes: Optional[str] = None) -> None:
        """Finish the current ETL run."""
        if not self.run_id:
            raise ValueError("No active run to finish")
        
        conn = get_conn(self.cfg)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update keap_meta.etl_run_log
                    set finished_at = now(), status = %s, notes = %s
                    where id = %s
                    """,
                    (status, notes, self.run_id)
                )
                conn.commit()
        finally:
            conn.close()
    
    def log_request(self, endpoint: str, page_offset: int, page_limit: int,
                   http_status: int, item_count: int, duration_ms: int,
                   throttled: bool = False, error: Optional[str] = None) -> None:
        """Log a request to the ETL request log."""
        if not self.run_id:
            raise ValueError("No active run to log request to")
        
        conn = get_conn(self.cfg)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into keap_meta.etl_request_log 
                    (run_id, endpoint, page_offset, page_limit, http_status, item_count, duration_ms, throttled, error)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (self.run_id, endpoint, page_offset, page_limit, http_status, 
                     item_count, duration_ms, throttled, error)
                )
                conn.commit()
        finally:
            conn.close()
    
    def record_source_count(self, entity: str, items_retrieved: int) -> None:
        """Record the number of items retrieved for an entity."""
        if not self.run_id:
            raise ValueError("No active run to record source count to")
        
        conn = get_conn(self.cfg)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into keap_meta.source_counts (run_id, entity, items_retrieved)
                    values (%s, %s, %s)
                    on conflict (run_id, entity) do update set
                        items_retrieved = excluded.items_retrieved
                    """,
                    (self.run_id, entity, items_retrieved)
                )
                conn.commit()
        finally:
            conn.close()
    
    def snapshot_tables(self) -> None:
        """Create table snapshots for the current run."""
        if not self.run_id:
            raise ValueError("No active run to snapshot tables for")
        
        conn = get_conn(self.cfg)
        try:
            with conn.cursor() as cur:
                # Get all keap schema tables
                cur.execute(
                    """
                    select table_schema, table_name
                    from information_schema.tables
                    where table_schema = 'keap' and table_type = 'BASE TABLE'
                    order by table_name
                    """
                )
                tables = cur.fetchall()
                
                for schema_name, table_name in tables:
                    # Get table digest
                    cur.execute(
                        """
                        select * from keap_meta.table_digest(%s, %s)
                        """,
                        (schema_name, table_name)
                    )
                    digest = cur.fetchone()
                    
                    if digest:
                        row_count, id_min, id_max, checksum_md5 = digest
                        
                        # Insert snapshot
                        cur.execute(
                            """
                            insert into keap_meta.table_snapshot 
                            (run_id, schema_name, table_name, row_count, id_min, id_max, checksum_md5)
                            values (%s, %s, %s, %s, %s, %s, %s)
                            on conflict (run_id, schema_name, table_name) do update set
                                row_count = excluded.row_count,
                                id_min = excluded.id_min,
                                id_max = excluded.id_max,
                                checksum_md5 = excluded.checksum_md5,
                                taken_at = now()
                            """,
                            (self.run_id, schema_name, table_name, row_count, id_min, id_max, checksum_md5)
                        )
                
                conn.commit()
        finally:
            conn.close()
    
    def get_run_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the current run."""
        if not self.run_id:
            raise ValueError("No active run to get summary for")
        
        conn = get_conn(self.cfg)
        try:
            with conn.cursor() as cur:
                # Get run info
                cur.execute(
                    """
                    select started_at, finished_at, status, notes
                    from keap_meta.etl_run_log
                    where id = %s
                    """,
                    (self.run_id,)
                )
                run_info = cur.fetchone()
                
                # Get source counts
                cur.execute(
                    """
                    select entity, items_retrieved
                    from keap_meta.source_counts
                    where run_id = %s
                    order by entity
                    """,
                    (self.run_id,)
                )
                source_counts = dict(cur.fetchall())
                
                # Get request summary
                cur.execute(
                    """
                    select 
                        count(*) as total_requests,
                        sum(item_count) as total_items,
                        sum(duration_ms) as total_duration_ms,
                        count(case when throttled then 1 end) as throttled_requests,
                        count(case when error is not null then 1 end) as error_requests
                    from keap_meta.etl_request_log
                    where run_id = %s
                    """,
                    (self.run_id,)
                )
                request_summary = cur.fetchone()
                
                return {
                    'run_id': self.run_id,
                    'started_at': run_info[0].isoformat() if run_info[0] else None,
                    'finished_at': run_info[1].isoformat() if run_info[1] else None,
                    'status': run_info[2],
                    'notes': run_info[3],
                    'source_counts': source_counts,
                    'request_summary': {
                        'total_requests': request_summary[0] or 0,
                        'total_items': request_summary[1] or 0,
                        'total_duration_ms': request_summary[2] or 0,
                        'throttled_requests': request_summary[3] or 0,
                        'error_requests': request_summary[4] or 0
                    }
                }
        finally:
            conn.close()
    
    def get_previous_run_comparison(self) -> Dict[str, Any]:
        """Compare current run with previous run."""
        if not self.run_id:
            raise ValueError("No active run to compare")
        
        conn = get_conn(self.cfg)
        try:
            with conn.cursor() as cur:
                # Get current and previous run snapshots
                cur.execute(
                    """
                    with ranked as (
                        select table_name, row_count, run_id,
                               row_number() over (partition by table_name order by run_id desc) as rn
                        from keap_meta.table_snapshot
                        where schema_name = 'keap'
                    )
                    select 
                        cur.table_name,
                        cur.row_count as current_rows,
                        prev.row_count as previous_rows,
                        (cur.row_count - coalesce(prev.row_count, 0)) as delta
                    from ranked cur
                    left join ranked prev
                        on prev.table_name = cur.table_name and prev.rn = 2
                    where cur.rn = 1
                    order by cur.table_name
                    """,
                    (self.run_id,)
                )
                comparisons = cur.fetchall()
                
                return {
                    'table_comparisons': [
                        {
                            'table_name': row[0],
                            'current_rows': row[1],
                            'previous_rows': row[2],
                            'delta': row[3]
                        }
                        for row in comparisons
                    ]
                }
        finally:
            conn.close()

def get_etl_tracker(cfg: Settings) -> ETLMetadataTracker:
    """Get a configured ETLMetadataTracker instance."""
    return ETLMetadataTracker(cfg)
