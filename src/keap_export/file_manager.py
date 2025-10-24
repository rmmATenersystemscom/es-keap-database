"""
File Manager for Keap Contact File Box Items
Handles downloading, storing, and managing contact files.
"""

from __future__ import annotations
import os
import hashlib
import mimetypes
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import psycopg2
from .config import Settings
from .client import KeapClient
from .retry import KeapRetryHandler

class FileManager:
    """Manages contact file downloads and storage."""
    
    def __init__(self, cfg: Settings, storage_dir: str = "files"):
        self.cfg = cfg
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.client = KeapClient(cfg)
        self.retry_handler = KeapRetryHandler(cfg)
        
        # Create subdirectories
        (self.storage_dir / "contacts").mkdir(exist_ok=True)
        (self.storage_dir / "temp").mkdir(exist_ok=True)
    
    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(
            host=self.cfg.db_host, port=self.cfg.db_port,
            dbname=self.cfg.db_name, user=self.cfg.db_user, password=self.cfg.db_password
        )
    
    def get_contact_files(self, contact_id: int) -> List[Dict[str, Any]]:
        """Get file list for a contact from Keap API."""
        try:
            response = self.client.request('GET', f'/crm/rest/v1/contacts/{contact_id}/files')
            return response.json().get('files', [])
        except Exception as e:
            print(f"Error fetching files for contact {contact_id}: {e}")
            return []
    
    def download_file(self, file_url: str, contact_id: int, file_name: str) -> Optional[str]:
        """Download a file and store it locally."""
        try:
            # Get file content
            response = requests.get(file_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Create contact-specific directory
            contact_dir = self.storage_dir / "contacts" / str(contact_id)
            contact_dir.mkdir(exist_ok=True)
            
            # Generate safe filename
            safe_filename = self._sanitize_filename(file_name)
            file_path = contact_dir / safe_filename
            
            # Handle filename conflicts
            counter = 1
            original_path = file_path
            while file_path.exists():
                name_parts = original_path.stem, counter, original_path.suffix
                file_path = original_path.parent / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                counter += 1
            
            # Download and save file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Get file metadata
            file_size = file_path.stat().st_size
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            return str(file_path)
            
        except Exception as e:
            print(f"Error downloading file {file_name}: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit filename length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def store_file_metadata(self, contact_id: int, file_name: str, file_path: str, 
                          file_size: int, mime_type: str, file_hash: str,
                          keap_file_id: str = None) -> int:
        """Store file metadata in database."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO keap.contact_files 
                    (contact_id, file_name, file_path, file_size, mime_type, file_hash, keap_file_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (contact_id, file_hash) DO UPDATE SET
                        file_name = EXCLUDED.file_name,
                        file_path = EXCLUDED.file_path,
                        file_size = EXCLUDED.file_size,
                        mime_type = EXCLUDED.mime_type,
                        updated_at = %s
                    RETURNING id
                """, (contact_id, file_name, file_path, file_size, mime_type, file_hash, 
                     keap_file_id, datetime.now(), datetime.now()))
                
                file_id = cur.fetchone()[0]
                conn.commit()
                return file_id
        finally:
            conn.close()
    
    def sync_contact_files(self, contact_id: int, download_files: bool = False) -> Dict[str, Any]:
        """Sync files for a specific contact."""
        print(f"Syncing files for contact {contact_id}...")
        
        # Get files from Keap API
        files = self.get_contact_files(contact_id)
        
        if not files:
            print(f"No files found for contact {contact_id}")
            return {"contact_id": contact_id, "files_found": 0, "files_downloaded": 0, "files_skipped": 0}
        
        files_downloaded = 0
        files_skipped = 0
        
        for file_info in files:
            file_name = file_info.get('file_name', 'unknown')
            file_url = file_info.get('file_url')
            keap_file_id = file_info.get('id')
            
            if not file_url:
                print(f"Skipping file {file_name} - no download URL")
                files_skipped += 1
                continue
            
            # Check if file already exists
            file_hash = self._calculate_remote_file_hash(file_url)
            if self._file_exists(contact_id, file_hash):
                print(f"File {file_name} already exists, skipping")
                files_skipped += 1
                continue
            
            if download_files:
                # Download file
                file_path = self.download_file(file_url, contact_id, file_name)
                if file_path:
                    # Store metadata
                    file_size = Path(file_path).stat().st_size
                    mime_type, _ = mimetypes.guess_type(file_path)
                    self.store_file_metadata(contact_id, file_name, file_path, 
                                           file_size, mime_type, file_hash, keap_file_id)
                    files_downloaded += 1
                    print(f"Downloaded: {file_name}")
                else:
                    files_skipped += 1
            else:
                # Just store metadata without downloading
                self.store_file_metadata(contact_id, file_name, file_url, 
                                       0, 'application/octet-stream', file_hash, keap_file_id)
                files_downloaded += 1
                print(f"Metadata stored: {file_name}")
        
        return {
            "contact_id": contact_id,
            "files_found": len(files),
            "files_downloaded": files_downloaded,
            "files_skipped": files_skipped
        }
    
    def _calculate_remote_file_hash(self, file_url: str) -> str:
        """Calculate hash of remote file without downloading."""
        try:
            response = requests.head(file_url, timeout=10)
            # Use URL + last_modified as hash
            last_modified = response.headers.get('last-modified', '')
            content_length = response.headers.get('content-length', '')
            hash_input = f"{file_url}_{last_modified}_{content_length}"
            return hashlib.sha256(hash_input.encode()).hexdigest()
        except:
            # Fallback to URL hash
            return hashlib.sha256(file_url.encode()).hexdigest()
    
    def _file_exists(self, contact_id: int, file_hash: str) -> bool:
        """Check if file already exists in database."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM keap.contact_files 
                    WHERE contact_id = %s AND file_hash = %s
                """, (contact_id, file_hash))
                return cur.fetchone() is not None
        finally:
            conn.close()
    
    def sync_all_contact_files(self, download_files: bool = False, limit: int = None) -> Dict[str, Any]:
        """Sync files for all contacts."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                query = "SELECT id FROM keap.contacts"
                if limit:
                    query += f" LIMIT {limit}"
                
                cur.execute(query)
                contact_ids = [row[0] for row in cur.fetchall()]
        finally:
            conn.close()
        
        total_files_found = 0
        total_files_downloaded = 0
        total_files_skipped = 0
        contacts_processed = 0
        
        for contact_id in contact_ids:
            result = self.sync_contact_files(contact_id, download_files)
            total_files_found += result['files_found']
            total_files_downloaded += result['files_downloaded']
            total_files_skipped += result['files_skipped']
            contacts_processed += 1
            
            if contacts_processed % 100 == 0:
                print(f"Processed {contacts_processed} contacts...")
        
        return {
            "contacts_processed": contacts_processed,
            "total_files_found": total_files_found,
            "total_files_downloaded": total_files_downloaded,
            "total_files_skipped": total_files_skipped
        }
    
    def list_contact_files(self, contact_id: int = None) -> List[Dict[str, Any]]:
        """List files for a contact or all contacts."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                if contact_id:
                    cur.execute("""
                        SELECT cf.*, c.given_name, c.family_name, c.email
                        FROM keap.contact_files cf
                        JOIN keap.contacts c ON cf.contact_id = c.id
                        WHERE cf.contact_id = %s
                        ORDER BY cf.created_at DESC
                    """, (contact_id,))
                else:
                    cur.execute("""
                        SELECT cf.*, c.given_name, c.family_name, c.email
                        FROM keap.contact_files cf
                        JOIN keap.contacts c ON cf.contact_id = c.id
                        ORDER BY cf.created_at DESC
                    """)
                
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()
    
    def cleanup_orphaned_files(self) -> int:
        """Remove files that no longer exist in Keap."""
        # This would require checking against Keap API
        # For now, just return 0
        return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_files,
                        SUM(file_size) as total_size,
                        COUNT(DISTINCT contact_id) as contacts_with_files,
                        AVG(file_size) as avg_file_size
                    FROM keap.contact_files
                """)
                
                result = cur.fetchone()
                return {
                    "total_files": result[0] or 0,
                    "total_size_bytes": result[1] or 0,
                    "total_size_mb": (result[1] or 0) / (1024 * 1024),
                    "contacts_with_files": result[2] or 0,
                    "avg_file_size_bytes": result[3] or 0
                }
        finally:
            conn.close()
