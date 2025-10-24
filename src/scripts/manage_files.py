#!/usr/bin/env python3
"""
File Management Script for Keap Contact Files
Manages downloading, storing, and organizing contact file box items.
"""

import sys
import os
import argparse
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keap_export.config import Settings
from keap_export.file_manager import FileManager

def main():
    """Main file management function."""
    parser = argparse.ArgumentParser(description="Manage Keap contact files")
    parser.add_argument("--sync", action="store_true",
                       help="Sync file metadata from Keap")
    parser.add_argument("--download", action="store_true",
                       help="Download files (requires --sync)")
    parser.add_argument("--contact-id", type=int,
                       help="Specific contact ID to process")
    parser.add_argument("--all-contacts", action="store_true",
                       help="Process all contacts")
    parser.add_argument("--limit", type=int,
                       help="Limit number of contacts to process")
    parser.add_argument("--list", action="store_true",
                       help="List files for contact or all contacts")
    parser.add_argument("--stats", action="store_true",
                       help="Show file storage statistics")
    parser.add_argument("--large-files", type=int, metavar="MB",
                       help="Find files larger than specified MB")
    parser.add_argument("--by-type", type=str,
                       help="List files of specific MIME type")
    parser.add_argument("--storage-dir", type=str, default="files",
                       help="Directory to store files (default: files)")
    parser.add_argument("--config", type=str, default=".env",
                       help="Path to configuration file (default: .env)")
    
    args = parser.parse_args()
    
    # Load configuration
    cfg = Settings()
    
    # Initialize file manager
    file_manager = FileManager(cfg, args.storage_dir)
    
    try:
        if args.stats:
            # Show file storage statistics
            stats = file_manager.get_storage_stats()
            print("=== File Storage Statistics ===")
            print(f"Total files: {stats['total_files']:,}")
            print(f"Total size: {stats['total_size_mb']:.2f} MB")
            print(f"Contacts with files: {stats['contacts_with_files']:,}")
            print(f"Average file size: {stats['avg_file_size_bytes']:.0f} bytes")
            return 0
        
        if args.large_files:
            # Find large files
            print(f"=== Files larger than {args.large_files} MB ===")
            conn = file_manager.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM keap.get_large_files(%s)", (args.large_files,))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                if rows:
                    print(f"{'Contact ID':<12} {'File Name':<30} {'Size (MB)':<10} {'Type':<20} {'Created'}")
                    print("-" * 90)
                    for row in rows:
                        contact_id, file_name, size_bytes, size_mb, mime_type, created_at = row
                        file_name_short = file_name[:28] + ".." if len(file_name) > 30 else file_name
                        print(f"{contact_id:<12} {file_name_short:<30} {size_mb:<10.2f} {mime_type or 'unknown':<20} {created_at.strftime('%Y-%m-%d')}")
                else:
                    print("No large files found")
            conn.close()
            return 0
        
        if args.by_type:
            # List files by type
            print(f"=== Files of type: {args.by_type} ===")
            conn = file_manager.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM keap.get_files_by_type(%s)", (args.by_type,))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                if rows:
                    print(f"{'Contact ID':<12} {'File Name':<30} {'Size (bytes)':<12} {'Created'}")
                    print("-" * 70)
                    for row in rows:
                        contact_id, file_name, size_bytes, file_path, created_at = row
                        file_name_short = file_name[:28] + ".." if len(file_name) > 30 else file_name
                        print(f"{contact_id:<12} {file_name_short:<30} {size_bytes:<12} {created_at.strftime('%Y-%m-%d')}")
                else:
                    print(f"No files of type {args.by_type} found")
            conn.close()
            return 0
        
        if args.list:
            # List files
            files = file_manager.list_contact_files(args.contact_id)
            if files:
                print(f"=== Contact Files ===")
                print(f"{'Contact ID':<12} {'Name':<20} {'Email':<30} {'File Name':<30} {'Size (MB)':<10} {'Type':<15} {'Created'}")
                print("-" * 120)
                for file_info in files:
                    contact_id = file_info['contact_id']
                    name = f"{file_info['given_name']} {file_info['family_name']}"[:19]
                    email = file_info['email'][:29] if file_info['email'] else 'N/A'
                    file_name = file_info['file_name'][:29] if len(file_info['file_name']) > 30 else file_info['file_name']
                    size_mb = file_info['file_size'] / (1024 * 1024) if file_info['file_size'] else 0
                    mime_type = file_info['mime_type'][:14] if file_info['mime_type'] else 'unknown'
                    created_at = file_info['created_at'].strftime('%Y-%m-%d')
                    
                    print(f"{contact_id:<12} {name:<20} {email:<30} {file_name:<30} {size_mb:<10.2f} {mime_type:<15} {created_at}")
            else:
                print("No files found")
            return 0
        
        if args.sync:
            # Sync files
            if args.contact_id:
                # Sync specific contact
                result = file_manager.sync_contact_files(args.contact_id, args.download)
                print(f"=== Sync Results for Contact {args.contact_id} ===")
                print(f"Files found: {result['files_found']}")
                print(f"Files {'downloaded' if args.download else 'metadata stored'}: {result['files_downloaded']}")
                print(f"Files skipped: {result['files_skipped']}")
            elif args.all_contacts:
                # Sync all contacts
                result = file_manager.sync_all_contact_files(args.download, args.limit)
                print(f"=== Sync Results ===")
                print(f"Contacts processed: {result['contacts_processed']}")
                print(f"Total files found: {result['total_files_found']}")
                print(f"Files {'downloaded' if args.download else 'metadata stored'}: {result['total_files_downloaded']}")
                print(f"Files skipped: {result['total_files_skipped']}")
            else:
                print("Error: --sync requires --contact-id or --all-contacts")
                return 1
            return 0
        
        # No action specified
        parser.print_help()
        return 1
        
    except Exception as e:
        print(f"File management failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
