# Keap Data Export Guide

This guide explains how to export data from the Keap database in various formats for external analysis, reporting, and integration.

## Overview

The export system supports multiple formats and export types:

- **CSV Export**: Human-readable format for Excel, Google Sheets, and basic analysis
- **Parquet Export**: Columnar format optimized for data analysis and big data tools
- **Analytics Export**: Pre-aggregated datasets with relationships and metrics
- **Bulk Export**: Export all entities at once

## Installation

The export functionality requires additional dependencies:

```bash
pip install pandas pyarrow
```

## Usage

### Basic Export Commands

```bash
# Export specific entity to CSV
python src/scripts/export_data.py --entity contacts --format csv

# Export specific entity to Parquet
python src/scripts/export_data.py --entity contacts --format parquet

# Export all entities
python src/scripts/export_data.py --all --format csv

# Export analytics dataset
python src/scripts/export_data.py --analytics --format parquet
```

### Advanced Options

```bash
# Export with filtering
python src/scripts/export_data.py --entity contacts --where "created_at > '2023-01-01'" --format csv

# Export with limit
python src/scripts/export_data.py --entity contacts --limit 1000 --format parquet

# Export to custom directory
python src/scripts/export_data.py --entity contacts --output-dir /path/to/exports --format csv

# List existing exports
python src/scripts/export_data.py --list

# Clean up old exports
python src/scripts/export_data.py --cleanup 30  # Remove files older than 30 days
```

## Export Types

### 1. Entity Exports

Export individual tables with all their data:

```bash
# Export contacts
python src/scripts/export_data.py --entity contacts --format csv

# Export companies
python src/scripts/export_data.py --entity companies --format parquet

# Export opportunities
python src/scripts/export_data.py --entity opportunities --format csv
```

**Available Entities:**
- `contacts` - Contact records with custom fields
- `companies` - Company records
- `opportunities` - Sales opportunities
- `tasks` - Task records
- `notes` - Note records
- `tags` - Tag definitions
- `users` - User records
- `products` - Product catalog
- `orders` - Order records
- `payments` - Payment records

### 2. Analytics Exports

Pre-aggregated datasets with relationships and metrics:

```bash
# Export analytics dataset
python src/scripts/export_data.py --analytics --format parquet
```

**Analytics Dataset Includes:**
- Contact information with company and owner details
- Opportunity counts and total values
- Task and note counts
- Tag associations
- Engagement metrics
- Timestamps for analysis

### 3. Bulk Exports

Export all entities at once:

```bash
# Export all entities to CSV
python src/scripts/export_data.py --all --format csv

# Export all entities to Parquet
python src/scripts/export_data.py --all --format parquet
```

## Output Formats

### CSV Format

- **Use Case**: Excel, Google Sheets, basic analysis
- **Advantages**: Human-readable, universal compatibility
- **File Extension**: `.csv`
- **Encoding**: UTF-8

### Parquet Format

- **Use Case**: Data analysis, big data tools, machine learning
- **Advantages**: Columnar storage, compression, type preservation
- **File Extension**: `.parquet`
- **Tools**: pandas, Apache Spark, Dask, R, etc.

## File Naming Convention

Exported files follow this naming pattern:

```
{entity}_{timestamp}.{format}
```

Examples:
- `contacts_20251024_010727.csv`
- `analytics_dataset_20251024_010736.parquet`
- `companies_20251024_010748.csv`

## Data Structure

### Contact Export

Includes all contact fields plus custom fields:

```csv
id,given_name,family_name,email,phone,address,city,state,postal_code,country_code,email_status,email_opted_in,score_value,created_at,updated_at,raw
```

### Analytics Export

Comprehensive dataset with relationships:

```csv
contact_id,given_name,family_name,email,email_status,email_opted_in,score_value,company_name,company_website,owner_email,owner_name,opportunity_count,task_count,note_count,tag_count,total_opportunity_value,created_at,updated_at
```

## Integration Examples

### Python Analysis

```python
import pandas as pd

# Load Parquet file
df = pd.read_parquet('exports/analytics_dataset_20251024_010736.parquet')

# Basic analysis
print(df.describe())
print(df.groupby('company_name').size())

# Filter and analyze
high_value_contacts = df[df['total_opportunity_value'] > 10000]
print(f"High-value contacts: {len(high_value_contacts)}")
```

### R Analysis

```r
library(arrow)
library(dplyr)

# Load Parquet file
df <- read_parquet('exports/analytics_dataset_20251024_010736.parquet')

# Basic analysis
summary(df)
df %>% group_by(company_name) %>% summarise(count = n())
```

### Excel/Google Sheets

1. Export to CSV format
2. Open in Excel or import to Google Sheets
3. Use pivot tables for analysis
4. Create charts and dashboards

## Performance Considerations

### Large Datasets

For large datasets, consider:

```bash
# Export with limit for testing
python src/scripts/export_data.py --entity contacts --limit 10000 --format parquet

# Use Parquet for better compression
python src/scripts/export_data.py --all --format parquet
```

### Memory Usage

- CSV exports use less memory
- Parquet exports are more efficient for large datasets
- Use `--limit` for testing with large datasets

## Automation

### Scheduled Exports

Create a cron job for regular exports:

```bash
# Daily analytics export at 2 AM
0 2 * * * cd /opt/es-keap-database && python src/scripts/export_data.py --analytics --format parquet

# Weekly full export on Sundays at 3 AM
0 3 * * 0 cd /opt/es-keap-database && python src/scripts/export_data.py --all --format parquet
```

### Cleanup Automation

```bash
# Clean up exports older than 30 days
0 4 * * * cd /opt/es-keap-database && python src/scripts/export_data.py --cleanup 30
```

## Troubleshooting

### Common Issues

1. **Memory errors with large datasets**
   - Use `--limit` to test with smaller datasets
   - Consider exporting entities individually

2. **Permission errors**
   - Ensure write permissions on output directory
   - Check disk space availability

3. **Missing dependencies**
   - Install required packages: `pip install pandas pyarrow`

### Performance Tips

1. Use Parquet for large datasets
2. Export during off-peak hours
3. Use `--limit` for testing
4. Clean up old exports regularly

## Examples

### Marketing Analysis

```bash
# Export contacts with engagement data
python src/scripts/export_data.py --analytics --format csv --where "email_opted_in = true"

# Export recent contacts
python src/scripts/export_data.py --entity contacts --where "created_at > '2024-01-01'" --format csv
```

### Sales Analysis

```bash
# Export opportunities with values
python src/scripts/export_data.py --entity opportunities --format parquet

# Export analytics for sales team
python src/scripts/export_data.py --analytics --format parquet
```

### Data Migration

```bash
# Export all data for migration
python src/scripts/export_data.py --all --format parquet

# Export specific entities
python src/scripts/export_data.py --entity contacts --format csv
python src/scripts/export_data.py --entity companies --format csv

---

**Version**: v1.0.0  
**Last Updated**: October 24, 2025 01:20 UTC  
**Maintainer**: Keap Database Team
```
