#!/usr/bin/env python3
"""
Sync tags from Keap API to PostgreSQL database.
"""

from __future__ import annotations
import argparse
import sys
from datetime import datetime
from typing import Optional

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '/opt/es-keap-database/src')

from keap_export.config import Settings
from keap_export.sync_base import create_sync
from keap_export.logger import get_logger

def main():
    """Main entry point for tags sync."""
    parser = argparse.ArgumentParser(description="Sync Keap Tags to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run without writing to the database")
    parser.add_argument("--since", type=str, 
                       help="Sync records updated since this ISO 8601 timestamp (e.g., 2023-01-01T00:00:00Z)")
    parser.add_argument("--config", type=str, default=".env",
                       help="Path to configuration file (default: .env)")
    
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
            logger.log_error("tags", f"Invalid --since timestamp format: {args.since}. Please use ISO 8601 (e.g., 2023-01-01T00:00:00Z).")
            return 1
    
    try:
        # Create sync instance
        sync = create_sync(cfg, 'tags')
        
        # Run sync
        count = sync.sync_entity(since=args.since, dry_run=args.dry_run)
        
        if args.dry_run:
            logger.log_info(f"Dry run completed: Would sync {count} tags")
        else:
            logger.log_info(f"Successfully synced {count} tags")
        
        return 0
        
    except Exception as e:
        logger.log_error("tags", f"Sync failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
