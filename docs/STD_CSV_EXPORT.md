# 📊 CSV Export Standards

**Purpose**: Define best practices for implementing CSV export functionality in dashboards  
**Scope**: All dashboard CSV export implementations  
**Compliance**: MANDATORY for all dashboards

---

## 🎯 Overview

This standard defines the implementation requirements for CSV export functionality in dashboards, including data formatting, error handling, user experience, and debugging capabilities.

---

## 📋 Core Requirements

### 1. Local Implementation
- ✅ **CSV export functions MUST be implemented locally in each dashboard**
- ✅ **NO global CSV utilities** - each dashboard handles its own CSV logic
- ✅ **Dashboard-specific data transformation** - handle unique data structures per dashboard

### 2. Function Naming Standards
```javascript
// Main export function (dashboard-specific)
exportCSV()                    // Main table export
exportModalCsv()              // Modal data export

// Helper functions (generic)
createCSVContent(headers, data)
escapeCSVField(field)
downloadCSVFile(content, filename)
```

### 3. Data Structure Requirements
- ✅ **Headers array**: Define column names clearly
- ✅ **Data array**: Ensure consistent data structure
- ✅ **Field mapping**: Map dashboard data to CSV columns
- ✅ **Null handling**: Handle missing/null values appropriately

---

## 🔧 Implementation Standards

### 1. CSV Content Creation
```javascript
function createCSVContent(headers, data) {
    // Create header row
    const headerRow = headers.map(escapeCSVField).join(',');
    
    // Create data rows
    const dataRows = data.map(item => {
        return headers.map(header => {
            const value = item[header] || item[header.toLowerCase()] || 'N/A';
            return escapeCSVField(value);
        }).join(',');
    });
    
    return [headerRow, ...dataRows].join('\n');
}
```

### 2. CSV Field Escaping
```javascript
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

#### Special Character Handling Examples
```javascript
// Test cases for field escaping
const testCases = [
    'Normal text',                    // → Normal text
    'Text with, comma',              // → "Text with, comma"
    'Text with "quotes"',            // → "Text with ""quotes"""
    'Text with\nnewline',            // → "Text with\nnewline"
    'Text with\rcarriage return',    // → "Text with\rcarriage return"
    'Text with\ttab',                // → "Text with\ttab"
    ' Leading space',                // → " Leading space"
    'Trailing space ',               // → "Trailing space "
    'Mixed "quotes", commas, and\nnewlines', // → "Mixed ""quotes"", commas, and\nnewlines"
    '',                              // → (empty string)
    null,                            // → (empty string)
    undefined                        // → (empty string)
];
```

### 3. File Download Implementation
```javascript
function downloadCSVFile(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}
```

---

## 🐛 Debugging Requirements

### 1. Console Logging (MANDATORY)
**Every CSV export function MUST log CSV content to the browser console for debugging purposes with flexible range options.**

```javascript
// Debug configuration options
const CSV_DEBUG_OPTIONS = {
    enabled: true,           // Enable/disable console logging
    mode: 'full',           // 'full', 'range', 'sample', 'truncated'
    range: {                // For 'range' mode
        start: 1,           // Start line (1-based)
        end: 100            // End line (1-based, or null for EOF)
    },
    sampleSize: 50,         // For 'sample' mode
    maxLines: 100           // For 'truncated' mode
};

function exportCSV() {
    // ... existing logic ...
    
    try {
        // Create CSV content
        const csvContent = createCSVContent(headers, data);
        
        // MANDATORY: Log CSV content for debugging
        logCSVContent(csvContent, CSV_DEBUG_OPTIONS);
        
        // Download CSV file
        downloadCSVFile(csvContent, filename);
        
    } catch (error) {
        console.error('Error exporting CSV:', error);
    }
}
```

### 2. Flexible Console Logging Function
```javascript
// Flexible CSV content logging function
function logCSVContent(csvContent, options) {
    if (!options.enabled) return;
    
    const lines = csvContent.split('\n');
    const totalLines = lines.length;
    
    console.log(`=== CSV EXPORT: ${totalLines} total lines ===`);
    
    switch (options.mode) {
        case 'full':
            console.log('=== CSV EXPORT CONTENT (FULL) ===');
            console.log(csvContent);
            console.log('=== END CSV EXPORT CONTENT ===');
            break;
            
        case 'range':
            const start = Math.max(0, (options.range.start || 1) - 1); // Convert to 0-based
            const end = options.range.end ? Math.min(totalLines, options.range.end) : totalLines;
            const rangeLines = lines.slice(start, end);
            
            console.log(`=== CSV EXPORT CONTENT (LINES ${start + 1}-${end}) ===`);
            console.log(rangeLines.join('\n'));
            console.log(`=== END CSV EXPORT CONTENT (${rangeLines.length} of ${totalLines} lines) ===`);
            break;
            
        case 'sample':
            const sampleSize = Math.min(options.sampleSize || 50, totalLines);
            const sampleLines = lines.slice(0, sampleSize);
            
            console.log(`=== CSV EXPORT CONTENT (SAMPLE - FIRST ${sampleSize} LINES) ===`);
            console.log(sampleLines.join('\n'));
            console.log(`=== END CSV EXPORT CONTENT (${sampleSize} of ${totalLines} lines) ===`);
            break;
            
        case 'truncated':
            const maxLines = Math.min(options.maxLines || 100, totalLines);
            const truncatedLines = lines.slice(0, maxLines);
            
            console.log(`=== CSV EXPORT CONTENT (TRUNCATED - FIRST ${maxLines} LINES) ===`);
            console.log(truncatedLines.join('\n'));
            console.log(`... (${totalLines - maxLines} more lines)`);
            console.log(`=== END CSV EXPORT CONTENT (${maxLines} of ${totalLines} lines) ===`);
            break;
    }
}
```

### 3. Console Log Format
- ✅ **Start marker**: `=== CSV EXPORT CONTENT ===`
- ✅ **CSV content**: Exact content that will be in the downloaded file
- ✅ **End marker**: `=== END CSV EXPORT CONTENT ===`
- ✅ **Same content**: Console log MUST match downloaded file content exactly

### 4. Debugging Usage Examples
```javascript
// Example 1: Full CSV logging (small datasets)
const DEBUG_FULL = {
    enabled: true,
    mode: 'full'
};

// Example 2: Range logging (lines 1-100)
const DEBUG_RANGE_START = {
    enabled: true,
    mode: 'range',
    range: { start: 1, end: 100 }
};

// Example 3: Range logging (lines 500 to end)
const DEBUG_RANGE_END = {
    enabled: true,
    mode: 'range',
    range: { start: 500, end: null } // null = EOF
};

// Example 4: Range logging (lines 100-200)
const DEBUG_RANGE_MIDDLE = {
    enabled: true,
    mode: 'range',
    range: { start: 100, end: 200 }
};

// Example 5: Sample logging (first 50 lines)
const DEBUG_SAMPLE = {
    enabled: true,
    mode: 'sample',
    sampleSize: 50
};

// Example 6: Truncated logging (first 100 lines)
const DEBUG_TRUNCATED = {
    enabled: true,
    mode: 'truncated',
    maxLines: 100
};

// Example 7: Disable logging
const DEBUG_DISABLED = {
    enabled: false
};
```

### 5. Performance Considerations
- ✅ **Safe limit**: < 1,000 lines for optimal performance
- ✅ **Warning threshold**: 1,000-2,000 lines may cause slight slowdown
- ✅ **Performance impact**: 2,000+ lines may cause browser issues
- ✅ **Large datasets**: Use 'range', 'sample', or 'truncated' modes

### 6. Debugging Benefits
- **Verification**: Confirm CSV content matches table data
- **Troubleshooting**: Identify data transformation issues
- **Quality assurance**: Ensure proper field escaping and formatting
- **Development**: Test CSV generation without downloading files
- **Flexible debugging**: Range logging for specific line segments
- **Performance optimization**: Truncated logging for large datasets

### 7. Browser Plugin Testing
**Use the browser plugin tool to leverage flexible debugging options:**

#### **Testing Workflow:**
1. **Navigate to dashboard** - Use browser plugin to access dashboard
2. **Monitor console output** - Watch flexible logging in real-time
3. **Test different modes** - Switch debugging configurations
4. **Verify CSV content** - Compare console output with downloaded files
5. **Performance testing** - Monitor browser performance with large datasets

#### **Debugging Mode Testing:**
```javascript
// Test 1: Full logging (small datasets)
const DEBUG_FULL = { enabled: true, mode: 'full' };
// Browser plugin: Monitor console for complete CSV content

// Test 2: Range logging (lines 1-50)
const DEBUG_RANGE = { 
    enabled: true, 
    mode: 'range', 
    range: { start: 1, end: 50 } 
};
// Browser plugin: Verify only lines 1-50 appear in console

// Test 3: Sample logging (first 25 lines)
const DEBUG_SAMPLE = { 
    enabled: true, 
    mode: 'sample', 
    sampleSize: 25 
};
// Browser plugin: Verify first 25 lines + line count

// Test 4: Truncated logging (first 100 lines)
const DEBUG_TRUNCATED = { 
    enabled: true, 
    mode: 'truncated', 
    maxLines: 100 
};
// Browser plugin: Verify first 100 lines + "... (X more lines)"
```

#### **Browser Plugin Advantages:**
- ✅ **Real-time monitoring** - See console output as it happens
- ✅ **Performance observation** - Monitor browser responsiveness
- ✅ **Content verification** - Compare console vs downloaded files
- ✅ **Mode switching** - Test different debugging configurations
- ✅ **Error detection** - Catch console errors and performance issues

#### **Practical Testing Example:**
```javascript
// Step 1: Navigate to dashboard using browser plugin
// Step 2: Set debugging mode in dashboard code
const CSV_DEBUG_OPTIONS = {
    enabled: true,
    mode: 'range',
    range: { start: 1, end: 50 }
};

// Step 3: Trigger CSV export via browser plugin
// Step 4: Monitor console output in browser plugin
// Expected output:
// === CSV EXPORT: 1000 total lines ===
// === CSV EXPORT CONTENT (LINES 1-50) ===
// name,user_count
// Organization 1,10
// Organization 2,20
// ...
// === END CSV EXPORT CONTENT (50 of 1000 lines) ===

// Step 5: Verify downloaded file contains full content
// Step 6: Compare console output with file content
// Step 7: Test different modes (full, sample, truncated)
```

### 5. Large Dataset Handling
For datasets with 1,000+ records, consider these alternatives:

```javascript
// Option 1: Truncated logging for large datasets
function exportCSV() {
    const csvContent = createCSVContent(headers, data);
    
    // Check line count before logging
    const lines = csvContent.split('\n');
    const lineCount = lines.length;
    
    // For large datasets, log first 100 lines + summary
    if (lineCount > 1000) {
        const truncated = lines.slice(0, 100).join('\n');
        console.log('=== CSV EXPORT CONTENT (FIRST 100 LINES) ===');
        console.log(truncated);
        console.log(`... (${lineCount - 100} more lines)`);
        console.log('=== END CSV CONTENT ===');
    } else {
        console.log('=== CSV EXPORT CONTENT ===');
        console.log(csvContent);
        console.log('=== END CSV CONTENT ===');
    }
    
    downloadCSVFile(csvContent, filename);
}

// Option 2: Sampling for debugging
function exportCSV() {
    const csvContent = createCSVContent(headers, data);
    
    // Log sample data for verification
    const lines = csvContent.split('\n');
    const sampleSize = Math.min(50, lines.length);
    const sample = lines.slice(0, sampleSize).join('\n');
    
    console.log('=== CSV EXPORT CONTENT (SAMPLE) ===');
    console.log(sample);
    console.log(`... (${lines.length - sampleSize} more lines)`);
    console.log('=== END CSV CONTENT ===');
    
    downloadCSVFile(csvContent, filename);
}

// Option 3: Check data size before CSV creation (most efficient)
function exportCSV() {
    // Check data size before creating CSV
    const dataSize = data.length;
    const expectedLines = dataSize + 1; // +1 for header
    
    console.log(`=== CSV EXPORT: ${dataSize} records, ${expectedLines} lines ===`);
    
    if (expectedLines > 1000) {
        console.log('Large dataset detected - using truncated logging');
        // Create CSV content
        const csvContent = createCSVContent(headers, data);
        
        // Log first 100 lines only
        const lines = csvContent.split('\n');
        const truncated = lines.slice(0, 100).join('\n');
        console.log('=== CSV EXPORT CONTENT (FIRST 100 LINES) ===');
        console.log(truncated);
        console.log(`... (${lines.length - 100} more lines)`);
        console.log('=== END CSV CONTENT ===');
        
        downloadCSVFile(csvContent, filename);
    } else {
        // Small dataset - log everything
        const csvContent = createCSVContent(headers, data);
        console.log('=== CSV EXPORT CONTENT ===');
        console.log(csvContent);
        console.log('=== END CSV CONTENT ===');
        downloadCSVFile(csvContent, filename);
    }
}
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
```javascript
// Handle different data types properly
function prepareFieldForCSV(field) {
    if (field === null || field === undefined) {
        return '';
    }
    
    // Handle different data types
    if (typeof field === 'boolean') {
        return field ? 'true' : 'false';
    }
    
    if (typeof field === 'number') {
        return field.toString();
    }
    
    if (typeof field === 'object') {
        // Handle arrays and objects
        if (Array.isArray(field)) {
            return field.join('; '); // Join array elements
        }
        return JSON.stringify(field); // Convert object to JSON string
    }
    
    return String(field);
}
```

---

## 🎨 User Experience Standards

### 1. Button States
```javascript
function exportCSV() {
    const buttonElement = document.getElementById('exportButton');
    
    // Store original state
    const originalText = buttonElement.textContent;
    const originalDisabled = buttonElement.disabled;
    
    // Update button state
    buttonElement.disabled = true;
    buttonElement.textContent = '📊 Exporting...';
    
    try {
        // CSV export logic
        const csvContent = createCSVContent(headers, data);
        console.log('=== CSV EXPORT CONTENT ===');
        console.log(csvContent);
        console.log('=== END CSV EXPORT CONTENT ===');
        downloadCSVFile(csvContent, filename);
        
    } catch (error) {
        console.error('Error exporting CSV:', error);
        alert('Error exporting CSV: ' + error.message);
    } finally {
        // Restore button state
        buttonElement.disabled = originalDisabled;
        buttonElement.textContent = originalText;
    }
}
```

### 2. Error Handling
- ✅ **Try-catch blocks**: Wrap all CSV operations
- ✅ **User feedback**: Alert users of errors
- ✅ **Console logging**: Log errors for debugging
- ✅ **Graceful degradation**: Handle missing data gracefully

### 3. Loading States
- ✅ **Button disabled**: Prevent multiple exports
- ✅ **Visual feedback**: Show "Exporting..." state
- ✅ **State restoration**: Restore original button state

---

## 📁 File Organization

### 1. File Structure
```
dashboard/
├── static/js/
│   ├── dashboard.js      # Main CSV export functions
│   ├── modal.js         # Modal CSV export functions
│   └── csv-export.js    # Shared CSV helper functions (optional)
```

### 2. Function Placement
- **Main exports**: In `dashboard.js` and `modal.js`
- **Helper functions**: Can be in separate `csv-export.js` or inline
- **No global utilities**: Keep all CSV logic local to dashboard

---

## ✅ Compliance Checklist

### Implementation
- [ ] CSV export functions implemented locally in dashboard
- [ ] No global CSV utilities used
- [ ] Function naming follows standards
- [ ] Data structure mapping correct
- [ ] Field escaping implemented properly
- [ ] RFC 4180 compliance verified
- [ ] Special characters handled (commas, quotes, newlines, tabs)
- [ ] Leading/trailing spaces handled
- [ ] Data type conversion implemented
- [ ] Null/undefined values handled

### Debugging
- [ ] Console logging implemented in ALL CSV functions
- [ ] Console log format follows standard
- [ ] Console content matches downloaded file exactly
- [ ] Error logging implemented
- [ ] Flexible logging options implemented (full, range, sample, truncated)
- [ ] Range logging supports start/end line specification
- [ ] Performance considerations addressed for large datasets
- [ ] Console logging optimized for dataset size

### User Experience
- [ ] Button loading states implemented
- [ ] Error handling with user feedback
- [ ] Graceful handling of missing data
- [ ] Proper file naming convention

### Testing
- [ ] CSV content verified against table data
- [ ] Console logs match downloaded files
- [ ] Error scenarios tested
- [ ] Loading states work correctly
- [ ] Browser plugin testing performed
- [ ] Flexible debugging modes tested
- [ ] Performance testing with large datasets
- [ ] Console output verification via browser plugin

---

## 🔗 Related Documentation

- **[STD_GLOBAL_FUNCTIONS.md](./STD_GLOBAL_FUNCTIONS.md)** - Function naming standards (SINGLE SOURCE OF TRUTH)
- **[STD_MODULAR_ARCHITECTURE.md](./STD_MODULAR_ARCHITECTURE.md)** - File organization standards (SINGLE SOURCE OF TRUTH)
- **[STD_DASHBOARD_LOADING.md](./STD_DASHBOARD_LOADING.md)** - Loading state management (SINGLE SOURCE OF TRUTH)
- **[STD_AI_RULES.md](./STD_AI_RULES.md)** - AI assistant rules and compliance requirements

---

**Version**: v1.0.0  
**Last Updated**: October 24, 2025 01:20 UTC  
**Maintainer**: Keap Database Team
