# Keap Export UI

Read-only interface to verify Keap → PostgreSQL export data, spot-check records, and surface gaps/validation results.

## Features

- **Overview Dashboard**: Entity counts, sync health, data integrity metrics
- **Entity Browser**: Browse and search through synced entities
- **Record Inspector**: Side-by-side comparison of Keap vs PostgreSQL records
- **ETL Runs**: View ETL run history and performance metrics
- **Validation Results**: Check for data integrity issues (orphans, duplicates)

## Quick Start

### Prerequisites

- Python 3.8+
- Access to the Keap Database PostgreSQL instance
- Valid Keap API tokens

### Installation

1. Install dependencies:
```bash
cd /opt/es-keap-database/ui/streamlit
pip install -r requirements.txt
```

2. Ensure environment variables are set in `/opt/es-keap-database/.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=keap
DB_USER=postgres
DB_PASSWORD=your_password
```

3. Ensure Keap tokens are available at `/opt/es-keap-database/.keap_tokens.json`

### Running the Application

```bash
cd /opt/es-keap-database/ui/streamlit
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

### Overview Dashboard
- View entity counts and sync status
- Check last ETL run performance
- Monitor data integrity metrics

### Entity Browser
- Select an entity (contacts, companies, etc.)
- Search and filter records
- View paginated results

### Record Inspector
- Enter an entity type and record ID
- Compare Keap live data vs PostgreSQL data
- See field-by-field differences with visual indicators

### ETL Runs
- View historical ETL run performance
- Check request metrics and throttle status
- Analyze sync duration and success rates

### Validation Results
- Check for orphaned records
- Identify duplicate emails
- View data integrity issues

## Security

- **Read-only**: No write operations to Keap or PostgreSQL
- **Token-based**: Uses existing Keap API tokens
- **Network isolation**: Respects existing firewall rules
- **No authentication**: Internal tool for operators

## Architecture

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Direct PostgreSQL and Keap API connections
- **Data Sources**: 
  - PostgreSQL (`keap.*` tables)
  - Keap API (live data)
  - ETL metadata (`keap_meta.*` tables)

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection parameters in `.env`
   - Ensure database exists and is accessible

2. **Keap API Errors**
   - Verify tokens are valid and not expired
   - Check network connectivity to Keap API
   - Review API rate limits

3. **No ETL Runs Found**
   - Run a sync operation first: `python src/scripts/sync_all.py`
   - Check ETL metadata is enabled in configuration

### Performance

- **Large datasets**: Use pagination and filters
- **API limits**: Respects Keap API rate limits
- **Database queries**: Optimized with proper indexing

## Development

### Adding New Features

1. **New Entity Support**: Add to entity lists in `app.py`
2. **Additional Validations**: Extend `get_validation_results()` method
3. **Custom Comparisons**: Modify `compare_records()` method

### Testing

```bash
# Test database connection
python -c "from app import KeapExportUI; ui = KeapExportUI(); print(ui.get_entity_counts())"

# Test Keap API connection
python -c "from app import KeapExportUI; ui = KeapExportUI(); print(ui.fetch_keap_record('contacts', '12345'))"
```

## Support

For issues or questions:
1. Check the logs in the Streamlit interface
2. Verify database and API connectivity
3. Review the main project documentation
