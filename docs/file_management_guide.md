# Keap File Management Guide

This guide explains how to manage contact file box items from Keap, including downloading, storing, and organizing files.

## Overview

The file management system provides:

- **File Discovery**: Find files associated with contacts in Keap
- **Metadata Storage**: Store file information in the database
- **File Downloads**: Optionally download files to local storage
- **File Organization**: Organize files by contact and type
- **Storage Management**: Monitor storage usage and cleanup

## Features

### File Storage
- **Local Storage**: Files stored in organized directory structure
- **Metadata Database**: File information stored in PostgreSQL
- **Deduplication**: Prevent duplicate downloads using file hashes
- **Type Detection**: Automatic MIME type detection
- **Size Tracking**: Monitor storage usage and file sizes

### File Organization
- **Contact-based**: Files organized by contact ID
- **Type-based**: Files categorized by MIME type
- **Size-based**: Find large files for cleanup
- **Date-based**: Track file creation and modification dates

## Usage

### Basic Commands

```bash
# Show file storage statistics
python src/scripts/manage_files.py --stats

# List all files
python src/scripts/manage_files.py --list

# Sync files for a specific contact (metadata only)
python src/scripts/manage_files.py --sync --contact-id 12345

# Sync and download files for a specific contact
python src/scripts/manage_files.py --sync --download --contact-id 12345

# Sync files for all contacts (metadata only)
python src/scripts/manage_files.py --sync --all-contacts

# Sync and download files for all contacts
python src/scripts/manage_files.py --sync --download --all-contacts
```

### Advanced Commands

```bash
# Find large files (>10MB)
python src/scripts/manage_files.py --large-files 10

# List files by type
python src/scripts/manage_files.py --by-type "application/pdf"

# Limit number of contacts processed
python src/scripts/manage_files.py --sync --all-contacts --limit 100

# Use custom storage directory
python src/scripts/manage_files.py --storage-dir /path/to/files --sync --all-contacts
```

## File Storage Structure

### Directory Layout

```
files/
├── contacts/
│   ├── 12345/
│   │   ├── document1.pdf
│   │   ├── image1.jpg
│   │   └── spreadsheet.xlsx
│   └── 67890/
│       ├── contract.pdf
│       └── photo.png
└── temp/
    └── (temporary files)
```

### Database Schema

**`keap.contact_files`** - File metadata:
- `id` - Primary key
- `contact_id` - Reference to contact
- `file_name` - Original filename
- `file_path` - Local file path
- `file_size` - File size in bytes
- `mime_type` - MIME type
- `file_hash` - SHA256 hash for deduplication
- `keap_file_id` - Keap API file ID
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

**`keap.file_download_log`** - Download operations:
- `id` - Primary key
- `contact_id` - Contact ID
- `operation` - Operation type
- `files_found` - Files discovered
- `files_downloaded` - Files downloaded
- `files_skipped` - Files skipped
- `total_size_bytes` - Total size processed
- `duration_ms` - Operation duration
- `error_message` - Error details
- `created_at` - Operation timestamp

## File Types Supported

### Common File Types
- **Documents**: PDF, DOC, DOCX, TXT, RTF
- **Images**: JPG, PNG, GIF, BMP, TIFF
- **Spreadsheets**: XLS, XLSX, CSV
- **Presentations**: PPT, PPTX
- **Archives**: ZIP, RAR, 7Z
- **Other**: Any file type supported by Keap

### MIME Type Detection
The system automatically detects MIME types for:
- Proper file organization
- Content filtering
- Storage optimization
- Security considerations

## Storage Management

### Monitoring Storage Usage

```bash
# Get storage statistics
python src/scripts/manage_files.py --stats
```

**Sample Output:**
```
=== File Storage Statistics ===
Total files: 1,250
Total size: 2.5 GB
Contacts with files: 150
Average file size: 2.1 MB
```

### Finding Large Files

```bash
# Find files larger than 10MB
python src/scripts/manage_files.py --large-files 10
```

**Sample Output:**
```
=== Files larger than 10 MB ===
Contact ID   File Name                    Size (MB)   Type                Created
12345        large_document.pdf          15.2        application/pdf     2024-01-15
67890        presentation.pptx           12.8        application/vnd...  2024-01-20
```

### Files by Type

```bash
# List PDF files
python src/scripts/manage_files.py --by-type "application/pdf"
```

## File Operations

### Metadata-Only Sync
- **Purpose**: Store file information without downloading
- **Use Case**: Inventory, reporting, analysis
- **Benefits**: Fast, low storage, comprehensive view
- **Command**: `--sync` (without `--download`)

### Full Download Sync
- **Purpose**: Download and store files locally
- **Use Case**: Backup, offline access, analysis
- **Benefits**: Complete file access, offline capability
- **Command**: `--sync --download`

### File Deduplication
- **Method**: SHA256 hash comparison
- **Scope**: Per-contact deduplication
- **Benefits**: Storage efficiency, prevents duplicates
- **Implementation**: Automatic during sync

## Performance Considerations

### Large Datasets
For large numbers of contacts:

```bash
# Process in batches
python src/scripts/manage_files.py --sync --all-contacts --limit 1000

# Use metadata-only for initial inventory
python src/scripts/manage_files.py --sync --all-contacts
```

### Storage Optimization
- **Compression**: Files stored as-is (no compression)
- **Deduplication**: Automatic hash-based deduplication
- **Cleanup**: Manual cleanup of old files
- **Monitoring**: Regular storage usage checks

### Network Considerations
- **Bandwidth**: Download operations use significant bandwidth
- **Rate Limiting**: Respects Keap API rate limits
- **Retry Logic**: Automatic retry on network errors
- **Timeout**: Configurable timeout settings

## Security Considerations

### File Access
- **Permissions**: Files stored with appropriate permissions
- **Access Control**: Database-level access control
- **Audit Trail**: Download operations logged
- **Encryption**: Files stored unencrypted (consider encryption for sensitive data)

### Data Protection
- **Backup**: Regular backups of file storage
- **Retention**: Configurable file retention policies
- **Cleanup**: Regular cleanup of old files
- **Monitoring**: Storage usage monitoring

## Automation

### Scheduled File Sync

```bash
# Daily file sync (metadata only)
0 2 * * * cd /opt/es-keap-database && python src/scripts/manage_files.py --sync --all-contacts

# Weekly file download
0 3 * * 0 cd /opt/es-keap-database && python src/scripts/manage_files.py --sync --download --all-contacts
```

### Storage Monitoring

```bash
# Daily storage check
0 4 * * * cd /opt/es-keap-database && python src/scripts/manage_files.py --stats >> /var/log/file-storage.log
```

## Troubleshooting

### Common Issues

1. **API Errors**
   - Check Keap API credentials
   - Verify network connectivity
   - Check rate limiting

2. **Storage Issues**
   - Monitor disk space
   - Check file permissions
   - Verify directory structure

3. **Download Failures**
   - Check file URLs
   - Verify network connectivity
   - Check file permissions

### Performance Issues

1. **Slow Downloads**
   - Use metadata-only sync for initial inventory
   - Download files in batches
   - Check network bandwidth

2. **Storage Full**
   - Clean up old files
   - Use file deduplication
   - Monitor storage usage

### Debugging

```bash
# Enable verbose logging
export PYTHONPATH=/opt/es-keap-database/src
python src/scripts/manage_files.py --sync --contact-id 12345 --verbose
```

## Examples

### Initial Setup

```bash
# 1. Get storage statistics
python src/scripts/manage_files.py --stats

# 2. Sync metadata for all contacts
python src/scripts/manage_files.py --sync --all-contacts

# 3. Check what files are available
python src/scripts/manage_files.py --list

# 4. Download files for specific contacts
python src/scripts/manage_files.py --sync --download --contact-id 12345
```

### Regular Maintenance

```bash
# 1. Check storage usage
python src/scripts/manage_files.py --stats

# 2. Find large files
python src/scripts/manage_files.py --large-files 50

# 3. Sync new files
python src/scripts/manage_files.py --sync --all-contacts

# 4. Download important files
python src/scripts/manage_files.py --sync --download --contact-id 12345
```

### Data Analysis

```bash
# 1. List all PDF files
python src/scripts/manage_files.py --by-type "application/pdf"

# 2. Find large files for cleanup
python src/scripts/manage_files.py --large-files 100

# 3. Get storage statistics
python src/scripts/manage_files.py --stats
```

## Integration

### Database Queries

```sql
-- Get files for a specific contact
SELECT * FROM keap.contact_files WHERE contact_id = 12345;

-- Get storage statistics
SELECT * FROM keap.get_file_stats();

-- Find large files
SELECT * FROM keap.get_large_files(10);
```

### Export Integration

```bash
# Export file metadata to CSV
python src/scripts/export_data.py --entity contact_files --format csv

# Export file metadata to Parquet
python src/scripts/export_data.py --entity contact_files --format parquet
```

This file management system provides comprehensive capabilities for managing contact files from Keap, with options for both metadata storage and full file downloads.

---

**Version**: v1.0.0  
**Last Updated**: October 24, 2025 01:20 UTC  
**Maintainer**: Keap Database Team
