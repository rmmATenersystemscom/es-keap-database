#!/usr/bin/env python3
"""
Data Export Script for Keap Database
Exports data in CSV and Parquet formats for external analysis.
"""

import sys
import os
import argparse
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keap_export.config import Settings
from keap_export.exporters import ExportManager

def main():
    """Main export function."""
    parser = argparse.ArgumentParser(description="Export Keap data in various formats")
    parser.add_argument("--format", choices=["csv", "parquet"], default="csv",
                       help="Export format (default: csv)")
    parser.add_argument("--entity", type=str,
                       help="Specific entity to export (e.g., contacts, companies)")
    parser.add_argument("--all", action="store_true",
                       help="Export all entities")
    parser.add_argument("--analytics", action="store_true",
                       help="Export analytics dataset")
    parser.add_argument("--output-dir", type=str, default="exports",
                       help="Output directory for exported files")
    parser.add_argument("--where", type=str,
                       help="WHERE clause for filtering data (e.g., 'created_at > \\'2023-01-01\\'')")
    parser.add_argument("--limit", type=int,
                       help="Limit number of records to export")
    parser.add_argument("--list", action="store_true",
                       help="List existing export files")
    parser.add_argument("--cleanup", type=int, metavar="DAYS",
                       help="Clean up export files older than specified days")
    parser.add_argument("--config", type=str, default=".env",
                       help="Path to configuration file (default: .env)")
    
    args = parser.parse_args()
    
    # Load configuration
    cfg = Settings()
    
    # Initialize export manager
    export_manager = ExportManager(cfg, args.output_dir)
    
    try:
        if args.list:
            # List existing export files
            files = export_manager.list_exported_files()
            if files:
                print("Existing export files:")
                for file_path in files:
                    print(f"  {file_path}")
            else:
                print("No export files found")
            return 0
        
        if args.cleanup:
            # Clean up old export files
            export_manager.cleanup_old_exports(args.cleanup)
            return 0
        
        if args.analytics:
            # Export analytics dataset
            print(f"Exporting analytics dataset in {args.format} format...")
            filepath = export_manager.export_analytics(args.format, args.limit)
            if filepath:
                print(f"Analytics export completed: {filepath}")
            return 0
        
        if args.all:
            # Export all entities
            print(f"Exporting all entities in {args.format} format...")
            exported_files = export_manager.export_all(args.format, args.where, args.limit)
            print(f"Exported {len(exported_files)} entities:")
            for file_path in exported_files:
                print(f"  {file_path}")
            return 0
        
        if args.entity:
            # Export specific entity
            print(f"Exporting {args.entity} in {args.format} format...")
            filepath = export_manager.export_entity(args.entity, args.format, args.where, args.limit)
            if filepath:
                print(f"Export completed: {filepath}")
            return 0
        
        # No action specified
        parser.print_help()
        return 1
        
    except Exception as e:
        print(f"Export failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
