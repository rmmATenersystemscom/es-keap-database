# 📊 CSV Export Standards

**Purpose**: Define best practices for implementing CSV export functionality in the Keap Database project  
**Scope**: All CSV export implementations for Keap data export system  
**Compliance**: MANDATORY for all export functionality

---

## 🎯 Overview

This standard defines the implementation requirements for CSV export functionality in the Keap Database project, including data formatting, error handling, logging, and debugging capabilities for backend data export operations.

---

## 📋 Core Requirements

### 1. Backend Implementation
- ✅ **CSV export functions MUST be implemented in the export system**
- ✅ **Centralized export utilities** - shared CSV logic in `src/keap_export/exporters.py`
- ✅ **Entity-specific data transformation** - handle unique data structures per Keap entity

### 2. Function Naming Standards
```python
# Main export functions (entity-specific)
export_contacts_csv()         # Contacts export
export_companies_csv()       # Companies export
export_opportunities_csv()   # Opportunities export

# Helper functions (generic)
create_csv_content(headers, data)
escape_csv_field(field)
write_csv_file(content, filename)
```

### 3. Data Structure Requirements
- ✅ **Headers array**: Define column names clearly
- ✅ **Data array**: Ensure consistent data structure
- ✅ **Field mapping**: Map Keap entity data to CSV columns
- ✅ **Null handling**: Handle missing/null values appropriately

---

## 🔧 Implementation Standards

### 1. CSV Content Creation
```python
def create_csv_content(headers, data):
    """Create CSV content from headers and data."""
    # Create header row
    header_row = ','.join(escape_csv_field(header) for header in headers)
    
    # Create data rows
    data_rows = []
    for item in data:
        row = []
        for header in headers:
            value = item.get(header) or item.get(header.lower()) or 'N/A'
            row.append(escape_csv_field(value))
        data_rows.append(','.join(row))
    
    return '\n'.join([header_row] + data_rows)
```

### 2. CSV Field Escaping
```python
def escape_csv_field(field):
    """Escape CSV field according to RFC 4180 standards."""
    # Handle None values
    if field is None:
        return ''
    
    # Convert to string
    string_field = str(field)
    
    # Check if field needs quoting (contains special characters)
    needs_quoting = (',' in string_field or 
                    '\n' in string_field or 
                    '\r' in string_field or 
                    '"' in string_field or
                    '\t' in string_field or
                    string_field.startswith(' ') or
                    string_field.endswith(' '))
    
    if needs_quoting:
        # Escape quotes by doubling them and wrap in quotes
        return '"' + string_field.replace('"', '""') + '"'
    
    return string_field
```

#### Special Character Handling Examples
```python
# Test cases for field escaping
test_cases = [
    'Normal text',                    # → Normal text
    'Text with, comma',              # → "Text with, comma"
    'Text with "quotes"',            # → "Text with ""quotes"""
    'Text with\nnewline',            # → "Text with\nnewline"
    'Text with\rcarriage return',    # → "Text with\rcarriage return"
    'Text with\ttab',                # → "Text with\ttab"
    ' Leading space',                # → " Leading space"
    'Trailing space ',               # → "Trailing space "
    'Mixed "quotes", commas, and\nnewlines', # → "Mixed ""quotes"", commas, and\nnewlines"
    '',                              # → (empty string)
    None,                            # → (empty string)
]
```

### 3. File Writing Implementation
```python
def write_csv_file(content, filename, output_dir='exports'):
    """Write CSV content to file."""
    import os
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"{filename}_{timestamp}.csv"
    filepath = os.path.join(output_dir, full_filename)
    
    # Write file with UTF-8 encoding
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath
```

---

## 🐛 Debugging Requirements

### 1. Logging (MANDATORY)
**Every CSV export function MUST log CSV content for debugging purposes with flexible range options.**

```python
# Debug configuration options
CSV_DEBUG_OPTIONS = {
    'enabled': True,           # Enable/disable logging
    'mode': 'full',           # 'full', 'range', 'sample', 'truncated'
    'range': {                # For 'range' mode
        'start': 1,           # Start line (1-based)
        'end': 100            # End line (1-based, or None for EOF)
    },
    'sample_size': 50,        # For 'sample' mode
    'max_lines': 100          # For 'truncated' mode
}

def export_csv():
    # ... existing logic ...
    
    try:
        # Create CSV content
        csv_content = create_csv_content(headers, data)
        
        # MANDATORY: Log CSV content for debugging
        log_csv_content(csv_content, CSV_DEBUG_OPTIONS)
        
        # Write CSV file
        filepath = write_csv_file(csv_content, filename)
        
    except Exception as error:
        print(f'Error exporting CSV: {error}')
```

### 2. Flexible Logging Function
```python
# Flexible CSV content logging function
def log_csv_content(csv_content, options):
    """Log CSV content with flexible options."""
    if not options.get('enabled', True):
        return
    
    lines = csv_content.split('\n')
    total_lines = len(lines)
    
    print(f"=== CSV EXPORT: {total_lines} total lines ===")
    
    mode = options.get('mode', 'full')
    
    if mode == 'full':
        print('=== CSV EXPORT CONTENT (FULL) ===')
        print(csv_content)
        print('=== END CSV EXPORT CONTENT ===')
        
    elif mode == 'range':
        start = max(0, (options.get('range', {}).get('start', 1) - 1))  # Convert to 0-based
        end = options.get('range', {}).get('end', total_lines)
        if end is None:
            end = total_lines
        end = min(total_lines, end)
        range_lines = lines[start:end]
        
        print(f"=== CSV EXPORT CONTENT (LINES {start + 1}-{end}) ===")
        print('\n'.join(range_lines))
        print(f"=== END CSV EXPORT CONTENT ({len(range_lines)} of {total_lines} lines) ===")
        
    elif mode == 'sample':
        sample_size = min(options.get('sample_size', 50), total_lines)
        sample_lines = lines[:sample_size]
        
        print(f"=== CSV EXPORT CONTENT (SAMPLE - FIRST {sample_size} LINES) ===")
        print('\n'.join(sample_lines))
        print(f"=== END CSV EXPORT CONTENT ({sample_size} of {total_lines} lines) ===")
        
    elif mode == 'truncated':
        max_lines = min(options.get('max_lines', 100), total_lines)
        truncated_lines = lines[:max_lines]
        
        print(f"=== CSV EXPORT CONTENT (TRUNCATED - FIRST {max_lines} LINES) ===")
        print('\n'.join(truncated_lines))
        print(f"... ({total_lines - max_lines} more lines)")
        print(f"=== END CSV EXPORT CONTENT ({max_lines} of {total_lines} lines) ===")
```

### 3. Log Format
- ✅ **Start marker**: `=== CSV EXPORT CONTENT ===`
- ✅ **CSV content**: Exact content that will be in the exported file
- ✅ **End marker**: `=== END CSV EXPORT CONTENT ===`
- ✅ **Same content**: Log output MUST match exported file content exactly

### 4. Debugging Usage Examples
```python
# Example 1: Full CSV logging (small datasets)
DEBUG_FULL = {
    'enabled': True,
    'mode': 'full'
}

# Example 2: Range logging (lines 1-100)
DEBUG_RANGE_START = {
    'enabled': True,
    'mode': 'range',
    'range': {'start': 1, 'end': 100}
}

# Example 3: Range logging (lines 500 to end)
DEBUG_RANGE_END = {
    'enabled': True,
    'mode': 'range',
    'range': {'start': 500, 'end': None}  # None = EOF
}

# Example 4: Range logging (lines 100-200)
DEBUG_RANGE_MIDDLE = {
    'enabled': True,
    'mode': 'range',
    'range': {'start': 100, 'end': 200}
}

# Example 5: Sample logging (first 50 lines)
DEBUG_SAMPLE = {
    'enabled': True,
    'mode': 'sample',
    'sample_size': 50
}

# Example 6: Truncated logging (first 100 lines)
DEBUG_TRUNCATED = {
    'enabled': True,
    'mode': 'truncated',
    'max_lines': 100
}

# Example 7: Disable logging
DEBUG_DISABLED = {
    'enabled': False
}
```

### 5. Performance Considerations
- ✅ **Safe limit**: < 1,000 lines for optimal performance
- ✅ **Warning threshold**: 1,000-2,000 lines may cause slight slowdown
- ✅ **Performance impact**: 2,000+ lines may cause memory issues
- ✅ **Large datasets**: Use 'range', 'sample', or 'truncated' modes

### 6. Debugging Benefits
- **Verification**: Confirm CSV content matches database data
- **Troubleshooting**: Identify data transformation issues
- **Quality assurance**: Ensure proper field escaping and formatting
- **Development**: Test CSV generation without writing files
- **Flexible debugging**: Range logging for specific line segments
- **Performance optimization**: Truncated logging for large datasets

### 7. Backend Testing
**Use command-line tools to test CSV export functionality:**

#### **Testing Workflow:**
1. **Run export command** - Execute CSV export from command line
2. **Monitor log output** - Watch flexible logging in real-time
3. **Test different modes** - Switch debugging configurations
4. **Verify CSV content** - Compare log output with exported files
5. **Performance testing** - Monitor system performance with large datasets

#### **Debugging Mode Testing:**
```python
# Test 1: Full logging (small datasets)
DEBUG_FULL = {'enabled': True, 'mode': 'full'}
# Command line: Monitor output for complete CSV content

# Test 2: Range logging (lines 1-50)
DEBUG_RANGE = { 
    'enabled': True, 
    'mode': 'range', 
    'range': {'start': 1, 'end': 50} 
}
# Command line: Verify only lines 1-50 appear in output

# Test 3: Sample logging (first 25 lines)
DEBUG_SAMPLE = { 
    'enabled': True, 
    'mode': 'sample', 
    'sample_size': 25 
}
# Command line: Verify first 25 lines + line count

# Test 4: Truncated logging (first 100 lines)
DEBUG_TRUNCATED = { 
    'enabled': True, 
    'mode': 'truncated', 
    'max_lines': 100 
}
# Command line: Verify first 100 lines + "... (X more lines)"
```

#### **Backend Testing Advantages:**
- ✅ **Real-time monitoring** - See log output as it happens
- ✅ **Performance observation** - Monitor system resource usage
- ✅ **Content verification** - Compare log vs exported files
- ✅ **Mode switching** - Test different debugging configurations
- ✅ **Error detection** - Catch errors and performance issues

#### **Practical Testing Example:**
```bash
# Step 1: Run export command
python src/scripts/export_data.py --entity contacts --format csv

# Step 2: Monitor log output
# Expected output:
# === CSV EXPORT: 1000 total lines ===
# === CSV EXPORT CONTENT (LINES 1-50) ===
# id,given_name,family_name,email
# 1,John,Doe,john@example.com
# 2,Jane,Smith,jane@example.com
# ...
# === END CSV EXPORT CONTENT (50 of 1000 lines) ===

# Step 3: Verify exported file contains full content
# Step 4: Compare log output with file content
# Step 5: Test different modes (full, sample, truncated)
```

### 8. Large Dataset Handling
For datasets with 1,000+ records, consider these alternatives:

```python
# Option 1: Truncated logging for large datasets
def export_csv():
    csv_content = create_csv_content(headers, data)
    
    # Check line count before logging
    lines = csv_content.split('\n')
    line_count = len(lines)
    
    # For large datasets, log first 100 lines + summary
    if line_count > 1000:
        truncated = '\n'.join(lines[:100])
        print('=== CSV EXPORT CONTENT (FIRST 100 LINES) ===')
        print(truncated)
        print(f"... ({line_count - 100} more lines)")
        print('=== END CSV CONTENT ===')
    else:
        print('=== CSV EXPORT CONTENT ===')
        print(csv_content)
        print('=== END CSV CONTENT ===')
    
    write_csv_file(csv_content, filename)

# Option 2: Sampling for debugging
def export_csv():
    csv_content = create_csv_content(headers, data)
    
    # Log sample data for verification
    lines = csv_content.split('\n')
    sample_size = min(50, len(lines))
    sample = '\n'.join(lines[:sample_size])
    
    print('=== CSV EXPORT CONTENT (SAMPLE) ===')
    print(sample)
    print(f"... ({len(lines) - sample_size} more lines)")
    print('=== END CSV CONTENT ===')
    
    write_csv_file(csv_content, filename)

# Option 3: Check data size before CSV creation (most efficient)
def export_csv():
    # Check data size before creating CSV
    data_size = len(data)
    expected_lines = data_size + 1  # +1 for header
    
    print(f"=== CSV EXPORT: {data_size} records, {expected_lines} lines ===")
    
    if expected_lines > 1000:
        print('Large dataset detected - using truncated logging')
        # Create CSV content
        csv_content = create_csv_content(headers, data)
        
        # Log first 100 lines only
        lines = csv_content.split('\n')
        truncated = '\n'.join(lines[:100])
        print('=== CSV EXPORT CONTENT (FIRST 100 LINES) ===')
        print(truncated)
        print(f"... ({len(lines) - 100} more lines)")
        print('=== END CSV CONTENT ===')
        
        write_csv_file(csv_content, filename)
    else:
        # Small dataset - log everything
        csv_content = create_csv_content(headers, data)
        print('=== CSV EXPORT CONTENT ===')
        print(csv_content)
        print('=== END CSV CONTENT ===')
        write_csv_file(csv_content, filename)
```

---

## 📋 CSV Format Compliance

### 1. RFC 4180 Standard Compliance
The CSV export must follow RFC 4180 standards for proper CSV formatting:

- ✅ **Field quoting**: Fields containing special characters must be quoted
- ✅ **Quote escaping**: Internal quotes must be doubled (`""`)
- ✅ **Line endings**: Use `\n` for line breaks
- ✅ **Field separation**: Use commas to separate fields
- ✅ **Header row**: First row contains column names

### 2. Edge Case Handling
```javascript
// Comprehensive field escaping for all edge cases
function escapeCSVField(field) {
    // Handle null/undefined values
    if (field === null || field === undefined) {
        return '';
    }
    
    // Convert to string
    const stringField = String(field);
    
    // Check if field needs quoting (contains special characters)
    const needsQuoting = stringField.includes(',') || 
                        stringField.includes('\n') || 
                        stringField.includes('\r') || 
                        stringField.includes('"') ||
                        stringField.includes('\t') ||
                        stringField.startsWith(' ') ||
                        stringField.endsWith(' ');
    
    if (needsQuoting) {
        // Escape quotes by doubling them and wrap in quotes
        return '"' + stringField.replace(/"/g, '""') + '"';
    }
    
    return stringField;
}
```

### 3. Data Type Handling
```python
# Handle different data types properly
def prepare_field_for_csv(field):
    """Prepare field for CSV export with proper type handling."""
    if field is None:
        return ''
    
    # Handle different data types
    if isinstance(field, bool):
        return 'true' if field else 'false'
    
    if isinstance(field, (int, float)):
        return str(field)
    
    if isinstance(field, (list, tuple)):
        # Handle arrays - join elements
        return '; '.join(str(item) for item in field)
    
    if isinstance(field, dict):
        # Handle objects - convert to JSON string
        import json
        return json.dumps(field)
    
    return str(field)
```

---

## 🎨 Backend Standards

### 1. Error Handling
```python
def export_csv():
    """Export CSV with proper error handling."""
    try:
        # CSV export logic
        csv_content = create_csv_content(headers, data)
        print('=== CSV EXPORT CONTENT ===')
        print(csv_content)
        print('=== END CSV EXPORT CONTENT ===')
        filepath = write_csv_file(csv_content, filename)
        print(f"CSV exported successfully to: {filepath}")
        
    except Exception as error:
        print(f'Error exporting CSV: {error}')
        raise
```

### 2. Error Handling Requirements
- ✅ **Try-catch blocks**: Wrap all CSV operations
- ✅ **Logging**: Log errors for debugging
- ✅ **Graceful degradation**: Handle missing data gracefully
- ✅ **File validation**: Verify file creation and content

### 3. Progress Reporting
- ✅ **Status messages**: Report export progress
- ✅ **File paths**: Display exported file locations
- ✅ **Record counts**: Show number of records exported
- ✅ **Performance metrics**: Report export duration and file size

---

## 📁 File Organization

### 1. File Structure
```
src/keap_export/
├── exporters.py         # Main CSV export functions
├── export_data.py       # CLI script for CSV exports
└── export_guide.md      # Export functionality documentation
```

### 2. Function Placement
- **Main exports**: In `exporters.py` with entity-specific functions
- **Helper functions**: Shared utilities in `exporters.py`
- **CLI interface**: Command-line script in `export_data.py`
- **Documentation**: Comprehensive guide in `export_guide.md`

---

## ✅ Compliance Checklist

### Implementation
- [ ] CSV export functions implemented in export system
- [ ] Centralized CSV utilities in `exporters.py`
- [ ] Function naming follows standards
- [ ] Data structure mapping correct
- [ ] Field escaping implemented properly
- [ ] RFC 4180 compliance verified
- [ ] Special characters handled (commas, quotes, newlines, tabs)
- [ ] Leading/trailing spaces handled
- [ ] Data type conversion implemented
- [ ] None values handled properly

### Debugging
- [ ] Logging implemented in ALL CSV functions
- [ ] Log format follows standard
- [ ] Log content matches exported file exactly
- [ ] Error logging implemented
- [ ] Flexible logging options implemented (full, range, sample, truncated)
- [ ] Range logging supports start/end line specification
- [ ] Performance considerations addressed for large datasets
- [ ] Logging optimized for dataset size

### Backend Standards
- [ ] Error handling with proper exception management
- [ ] Progress reporting implemented
- [ ] File validation and verification
- [ ] Performance metrics reporting
- [ ] Proper file naming convention with timestamps

### Testing
- [ ] CSV content verified against database data
- [ ] Log output matches exported files
- [ ] Error scenarios tested
- [ ] Command-line testing performed
- [ ] Flexible debugging modes tested
- [ ] Performance testing with large datasets
- [ ] Log output verification via command line

---

## 🔗 Related Documentation

- **[export_guide.md](./export_guide.md)** - Comprehensive export functionality guide
- **[file_management_guide.md](./file_management_guide.md)** - File management and download guide
- **[etl_tracker_migration.md](./etl_tracker_migration.md)** - ETL tracker migration guide
- **[implementation_story.md](./implementation_story.md)** - Project implementation documentation
- **[keap_api_reference.md](./keap_api_reference.md)** - Keap API reference documentation

---

**Version**: v1.0.1  
**Last Updated**: October 24, 2025 01:25 UTC  
**Maintainer**: Keap Database Team
