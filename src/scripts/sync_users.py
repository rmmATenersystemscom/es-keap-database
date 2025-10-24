#!/usr/bin/env python3
"""
Keap Users Sync CLI

Sync users from Keap API to PostgreSQL database.
Supports incremental sync with --since parameter and dry-run mode.
"""

import argparse
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, '/opt/es-keap-database/src')

from keap_export.config import Settings
from keap_export.sync_base import UserSync
from keap_export.etl_meta import get_etl_tracker
from keap_export.logger import get_logger

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Sync users from Keap API to PostgreSQL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full sync
  python -m src.scripts.sync_users
  
  # Incremental sync since specific date
  python -m src.scripts.sync_users --since 2024-01-15T10:30:00Z
  
  # Dry run (no database writes)
  python -m src.scripts.sync_users --dry-run
        """
    )
    
    parser.add_argument(
        '--since',
        type=str,
        help='Sync records modified since this ISO timestamp (e.g., 2024-01-15T10:30:00Z)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform dry run without writing to database'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()

def validate_since_timestamp(since: str) -> str:
    """Validate and normalize the since timestamp."""
    try:
        # Try to parse the timestamp
        dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        return dt.isoformat()
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format: {since}. Use ISO format like 2024-01-15T10:30:00Z") from e

def main():
    """Main entry point for users sync."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_arguments()
    
    # Validate since timestamp if provided
    since = None
    if args.since:
        since = validate_since_timestamp(args.since)
    
    # Load configuration
    cfg = Settings()
    
    # Set log level
    if args.verbose:
        cfg.log_level = 'DEBUG'
    
    # Initialize logger
    logger = get_logger(cfg)
    
    try:
        # Start ETL run tracking
        etl_tracker = get_etl_tracker(cfg)
        run_id = etl_tracker.start_run(f"Users sync - since: {since}, dry_run: {args.dry_run}")
        
        logger.log_info("Starting users sync", entity="users", 
                       since=since, dry_run=args.dry_run, run_id=run_id)
        
        # Create sync instance
        sync = UserSync(cfg)
        
        # Perform sync
        processed_count = sync.sync_entity(since=since, dry_run=args.dry_run)
        
        # Finish ETL run
        etl_tracker.finish_run('success', f"Processed {processed_count} users")
        
        # Get run summary
        summary = etl_tracker.get_run_summary()
        
        logger.log_info("Users sync completed successfully", 
                       entity="users", processed_count=processed_count, 
                       run_id=run_id, summary=summary)
        
        print(f"✅ Users sync completed: {processed_count} records processed")
        if args.dry_run:
            print("🔍 Dry run mode - no data was written to database")
        
        return 0
        
    except Exception as e:
        logger.log_error(f"Users sync failed: {e}", entity="users", error=str(e))
        print(f"❌ Users sync failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
