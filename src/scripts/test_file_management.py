#!/usr/bin/env python3
"""
Test script for file management functionality.
This script demonstrates the file management capabilities.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keap_export.config import Settings
from keap_export.file_manager import FileManager

def test_file_management():
    """Test the file management functionality."""
    cfg = Settings()
    file_manager = FileManager(cfg, "test_files")
    
    print("Testing file management functionality...")
    
    # Test 1: Get storage statistics
    print("\n1. Storage Statistics:")
    stats = file_manager.get_storage_stats()
    print(f"   Total files: {stats['total_files']}")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")
    print(f"   Contacts with files: {stats['contacts_with_files']}")
    
    # Test 2: List files (should be empty initially)
    print("\n2. Listing files:")
    files = file_manager.list_contact_files()
    print(f"   Found {len(files)} files")
    
    # Test 3: Simulate file metadata storage
    print("\n3. Simulating file metadata storage:")
    try:
        file_id = file_manager.store_file_metadata(
            contact_id=50907,
            file_name="test_document.pdf",
            file_path="/test/path/test_document.pdf",
            file_size=1024000,  # 1MB
            mime_type="application/pdf",
            file_hash="test_hash_123",
            keap_file_id="keap_123"
        )
        print(f"   Stored file metadata with ID: {file_id}")
    except Exception as e:
        print(f"   Error storing metadata: {e}")
    
    # Test 4: Check updated statistics
    print("\n4. Updated Statistics:")
    stats = file_manager.get_storage_stats()
    print(f"   Total files: {stats['total_files']}")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")
    
    # Test 5: List files again
    print("\n5. Listing files after adding metadata:")
    files = file_manager.list_contact_files()
    print(f"   Found {len(files)} files")
    for file_info in files:
        print(f"   - {file_info['file_name']} ({file_info['file_size']} bytes)")
    
    print("\nFile management test completed successfully!")

if __name__ == "__main__":
    test_file_management()
