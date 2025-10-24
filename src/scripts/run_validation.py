#!/usr/bin/env python3
"""
Run SQL validation queries after a sync run.
"""

from __future__ import annotations
import argparse
import sys
import psycopg2
from typing import Dict, Any, List

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, '/opt/es-keap-database/src')

from keap_export.config import Settings
from keap_export.db import get_conn
from keap_export.logger import get_logger

def run_validation_queries(cfg: Settings) -> Dict[str, Any]:
    """Run all validation queries and return results."""
    logger = get_logger(cfg)
    results = {}
    
    # Read validation SQL file
    try:
        with open('/opt/es-keap-database/sql/keap_validation.sql', 'r') as f:
            validation_sql = f.read()
    except FileNotFoundError:
        logger.log_error("validation", "Validation SQL file not found: sql/keap_validation.sql")
        return {}
    
    # Split into individual queries (assuming they're separated by --)
    queries = [q.strip() for q in validation_sql.split('--') if q.strip()]
    
    with get_conn(cfg) as conn:
        with conn.cursor() as cur:
            for i, query in enumerate(queries):
                if not query or query.startswith('/*') or query.startswith('*'):
                    continue
                    
                try:
                    logger.log_info(f"Running validation query {i+1}/{len(queries)}")
                    cur.execute(query)
                    
                    # Get results
                    if cur.description:
                        rows = cur.fetchall()
                        columns = [desc[0] for desc in cur.description]
                        results[f"query_{i+1}"] = {
                            'columns': columns,
                            'rows': rows,
                            'count': len(rows)
                        }
                    else:
                        results[f"query_{i+1}"] = {
                            'message': 'Query executed successfully',
                            'count': cur.rowcount
                        }
                        
                except Exception as e:
                    logger.log_error("validation", f"Query {i+1} failed: {e}")
                    results[f"query_{i+1}"] = {
                        'error': str(e),
                        'count': 0
                    }
    
    return results

def print_validation_summary(results: Dict[str, Any]):
    """Print a summary of validation results."""
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    total_issues = 0
    
    for query_name, result in results.items():
        if 'error' in result:
            print(f"❌ {query_name}: ERROR - {result['error']}")
            total_issues += 1
        elif result.get('count', 0) > 0:
            print(f"⚠️  {query_name}: {result['count']} issues found")
            total_issues += result['count']
        else:
            print(f"✅ {query_name}: No issues found")
    
    print("="*60)
    if total_issues == 0:
        print("🎉 All validations passed! Data integrity is good.")
    else:
        print(f"⚠️  Total issues found: {total_issues}")
    print("="*60)

def main():
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(description="Run data validation queries")
    parser.add_argument("--config", type=str, default=".env",
                       help="Path to configuration file (default: .env)")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed query results")
    
    args = parser.parse_args()
    
    # Load configuration
    cfg = Settings()
    logger = get_logger(cfg)
    
    try:
        logger.log_info("Starting data validation")
        results = run_validation_queries(cfg)
        
        if args.verbose:
            print("\nDETAILED RESULTS:")
            for query_name, result in results.items():
                print(f"\n{query_name}:")
                if 'error' in result:
                    print(f"  ERROR: {result['error']}")
                elif 'rows' in result:
                    print(f"  Columns: {result['columns']}")
                    print(f"  Rows: {result['count']}")
                    if result['rows']:
                        print("  Sample data:")
                        for row in result['rows'][:5]:  # Show first 5 rows
                            print(f"    {row}")
                else:
                    print(f"  {result.get('message', 'No data')}")
        
        print_validation_summary(results)
        
        # Return non-zero if any issues found
        total_issues = sum(
            result.get('count', 0) for result in results.values() 
            if 'error' not in result
        )
        
        return 1 if total_issues > 0 else 0
        
    except Exception as e:
        logger.log_error("validation", f"Validation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
