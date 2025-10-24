#!/usr/bin/env python3
"""
Master sync script that runs all Keap entity syncs in proper order.
"""

from __future__ import annotations
import argparse
import sys
import time
from datetime import datetime
from typing import Optional, List, Tuple

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '/opt/es-keap-database/src')

from keap_export.config import Settings
from keap_export.sync_base import create_sync
from keap_export.logger import get_logger
from keap_export.etl_meta import get_etl_tracker

# Define sync order: reference tables first, then main entities
SYNC_ORDER = [
    # Reference tables (no dependencies)
    'users',
    'tags',
    
    # Main entities (depend on reference tables)
    'companies',
    'contacts',
    'opportunities',
    'tasks',
    'notes',
    'products',
    'orders',
]

def run_sync_entity(cfg: Settings, entity: str, etl_tracker, since: Optional[str] = None, 
                   dry_run: bool = False) -> Tuple[bool, int, float]:
    """Run sync for a single entity."""
    logger = get_logger(cfg)
    start_time = time.time()
    
    try:
        logger.log_info(f"Starting sync for {entity}")
        sync = create_sync(cfg, entity)
        # Pass the shared ETL tracker to the sync
        count = sync.sync_entity(since=since, dry_run=dry_run, etl_tracker=etl_tracker)
        
        duration = time.time() - start_time
        logger.log_info(f"Completed sync for {entity}: {count} records in {duration:.2f}s")
        
        return True, count, duration
        
    except Exception as e:
        duration = time.time() - start_time
        logger.log_error(entity, f"Sync failed: {e}")
        return False, 0, duration

def main():
    """Main entry point for full sync."""
    parser = argparse.ArgumentParser(description="Sync all Keap entities to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run without writing to the database")
    parser.add_argument("--since", type=str, 
                       help="Sync records updated since this ISO 8601 timestamp (e.g., 2023-01-01T00:00:00Z)")
    parser.add_argument("--entities", type=str, nargs='+',
                       help="Specific entities to sync (default: all)")
    parser.add_argument("--config", type=str, default=".env",
                       help="Path to configuration file (default: .env)")
    parser.add_argument("--continue-on-error", action="store_true",
                       help="Continue syncing other entities if one fails")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from last successful checkpoint")
    
    args = parser.parse_args()
    
    # Load configuration
    cfg = Settings()
    logger = get_logger(cfg)
    
    # Parse since timestamp if provided
    since_dt: Optional[datetime] = None
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since.replace('Z', '+00:00'))
        except ValueError:
            logger.log_error("sync_all", f"Invalid --since timestamp format: {args.since}. Please use ISO 8601 (e.g., 2023-01-01T00:00:00Z).")
            return 1
    
    # Determine entities to sync
    entities_to_sync = args.entities if args.entities else SYNC_ORDER
    
    # Validate entities
    for entity in entities_to_sync:
        if entity not in SYNC_ORDER:
            logger.log_error("sync_all", f"Unknown entity: {entity}. Available: {', '.join(SYNC_ORDER)}")
            return 1
    
    # Sort entities according to sync order
    entities_to_sync = [e for e in SYNC_ORDER if e in entities_to_sync]
    
    logger.log_info(f"Starting full sync for {len(entities_to_sync)} entities: {', '.join(entities_to_sync)}")
    if args.dry_run:
        logger.log_info("Running in DRY RUN mode - no database writes will occur")
    
    # Create a single ETL run for the entire sync
    etl_tracker = get_etl_tracker(cfg)
    run_id = etl_tracker.start_run(f"Full sync: {', '.join(entities_to_sync)}")
    logger.log_info(f"ETL run started with ID: {run_id}")
    
    # Handle resume functionality
    if args.resume:
        # Look for the most recent interrupted run
        conn = etl_tracker._conn_autocommit()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rl.id, rl.started_at
                FROM keap_meta.etl_run_log rl
                WHERE rl.status = 'running'
                  AND rl.id != %s
                  AND EXISTS (
                      SELECT 1 FROM keap_meta.sync_progress sp 
                      WHERE sp.run_id = rl.id 
                        AND sp.status IN ('pending', 'running', 'failed')
                  )
                ORDER BY rl.started_at DESC
                LIMIT 1
            """, (run_id,))
            result = cur.fetchone()
            
            if result:
                interrupted_run_id = result[0]
                logger.log_info(f"Found interrupted run ID: {interrupted_run_id}")
                
                # Get entities to resume from the interrupted run
                cur.execute("""
                    SELECT entity_name FROM keap_meta.get_entities_to_resume(%s)
                """, (interrupted_run_id,))
                entities_to_resume = [row[0] for row in cur.fetchall()]
                
                if entities_to_resume:
                    logger.log_info(f"Resuming sync for entities: {', '.join(entities_to_resume)}")
                    entities_to_sync = entities_to_resume
                else:
                    logger.log_info("No entities found to resume")
                    return 0
            else:
                logger.log_info("No interrupted runs found to resume")
                return 0
    
    start_time = time.time()
    results = []
    failed_entities = []
    
    try:
        # Run sync for each entity
        for entity in entities_to_sync:
            success, count, duration = run_sync_entity(cfg, entity, etl_tracker, args.since, args.dry_run)
            results.append((entity, success, count, duration))
        
            if not success:
                failed_entities.append(entity)
                if not args.continue_on_error:
                    logger.log_error("sync_all", f"Sync failed for {entity}. Stopping.")
                    break
        
        # Summary
        total_duration = time.time() - start_time
        successful_entities = [r[0] for r in results if r[1]]
        total_records = sum(r[2] for r in results if r[1])
        
        logger.log_info(f"Sync completed in {total_duration:.2f}s")
        logger.log_info(f"Successful entities: {len(successful_entities)}/{len(entities_to_sync)}")
        logger.log_info(f"Total records processed: {total_records}")
        
        # End the ETL run
        etl_tracker.end_run(success=len(failed_entities) == 0, 
                           notes=f"Completed: {len(successful_entities)}/{len(entities_to_sync)} entities, {total_records} records")
        
        if failed_entities:
            logger.log_error("sync_all", f"Failed entities: {', '.join(failed_entities)}")
            return 1
        
        return 0
        
    except Exception as e:
        logger.log_error("sync_all", f"Unexpected error: {e}")
        etl_tracker.end_run(success=False, notes=f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
