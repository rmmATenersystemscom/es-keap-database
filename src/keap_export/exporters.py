"""
Data Export Module for Keap Database
Supports CSV and Parquet export formats for external analysis.
"""

from __future__ import annotations
import os
import csv
import json
import pandas as pd
import psycopg2
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from .config import Settings

class BaseExporter:
    """Base class for data exporters."""
    
    def __init__(self, cfg: Settings, output_dir: str = "exports"):
        self.cfg = cfg
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(
            host=self.cfg.db_host, port=self.cfg.db_port,
            dbname=self.cfg.db_name, user=self.cfg.db_user, password=self.cfg.db_password
        )
    
    def get_table_data(self, table_name: str, schema: str = "keap", 
                      where_clause: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get data from a database table."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                query = f"SELECT * FROM {schema}.{table_name}"
                params = []
                
                if where_clause:
                    query += f" WHERE {where_clause}"
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()
    
    def get_entity_tables(self) -> List[str]:
        """Get list of entity tables in the keap schema."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'keap' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

class CSVExporter(BaseExporter):
    """CSV export functionality."""
    
    def export_table(self, table_name: str, schema: str = "keap", 
                    where_clause: str = None, limit: int = None,
                    filename: str = None) -> str:
        """Export a single table to CSV."""
        data = self.get_table_data(table_name, schema, where_clause, limit)
        
        if not data:
            print(f"No data found for table {schema}.{table_name}")
            return None
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if data:
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        print(f"Exported {len(data)} records from {schema}.{table_name} to {filepath}")
        return str(filepath)
    
    def export_all_entities(self, where_clause: str = None, limit: int = None) -> List[str]:
        """Export all entity tables to CSV."""
        tables = self.get_entity_tables()
        exported_files = []
        
        for table in tables:
            try:
                filepath = self.export_table(table, where_clause=where_clause, limit=limit)
                if filepath:
                    exported_files.append(filepath)
            except Exception as e:
                print(f"Error exporting {table}: {e}")
                continue
        
        return exported_files
    
    def export_contacts_with_relationships(self, limit: int = None) -> str:
        """Export contacts with related data (companies, tags, etc.)."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        c.id,
                        c.given_name,
                        c.family_name,
                        c.email,
                        c.phone,
                        c.address,
                        c.city,
                        c.state,
                        c.postal_code,
                        c.country_code,
                        c.email_status,
                        c.email_opted_in,
                        c.score_value,
                        co.name as company_name,
                        co.website as company_website,
                        u.email as owner_email,
                        u.given_name as owner_name,
                        c.created_at,
                        c.updated_at
                    FROM keap.contacts c
                    LEFT JOIN keap.companies co ON c.company_id = co.id
                    LEFT JOIN keap.users u ON c.owner_id = u.id
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                data = [dict(zip(columns, row)) for row in rows]
                
                if not data:
                    print("No contact data found")
                    return None
                
                # Export to CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"contacts_with_relationships_{timestamp}.csv"
                filepath = self.output_dir / filename
                
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                
                print(f"Exported {len(data)} contacts with relationships to {filepath}")
                return str(filepath)
        finally:
            conn.close()

class ParquetExporter(BaseExporter):
    """Parquet export functionality."""
    
    def export_table(self, table_name: str, schema: str = "keap",
                    where_clause: str = None, limit: int = None,
                    filename: str = None) -> str:
        """Export a single table to Parquet."""
        data = self.get_table_data(table_name, schema, where_clause, limit)
        
        if not data:
            print(f"No data found for table {schema}.{table_name}")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Handle JSONB columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column contains JSON-like data
                sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if isinstance(sample_val, str) and (sample_val.startswith('{') or sample_val.startswith('[')):
                    try:
                        # Convert JSON strings to proper JSON objects
                        df[col] = df[col].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.parquet"
        
        filepath = self.output_dir / filename
        
        # Write Parquet file
        df.to_parquet(filepath, index=False, engine='pyarrow')
        
        print(f"Exported {len(data)} records from {schema}.{table_name} to {filepath}")
        return str(filepath)
    
    def export_all_entities(self, where_clause: str = None, limit: int = None) -> List[str]:
        """Export all entity tables to Parquet."""
        tables = self.get_entity_tables()
        exported_files = []
        
        for table in tables:
            try:
                filepath = self.export_table(table, where_clause=where_clause, limit=limit)
                if filepath:
                    exported_files.append(filepath)
            except Exception as e:
                print(f"Error exporting {table}: {e}")
                continue
        
        return exported_files
    
    def export_analytics_dataset(self, limit: int = None) -> str:
        """Export a comprehensive analytics dataset."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Create a comprehensive analytics view
                query = """
                    WITH contact_metrics AS (
                        SELECT 
                            c.id as contact_id,
                            c.given_name,
                            c.family_name,
                            c.email,
                            c.email_status,
                            c.email_opted_in,
                            c.score_value,
                            co.name as company_name,
                            co.website as company_website,
                            u.email as owner_email,
                            COUNT(DISTINCT o.id) as opportunity_count,
                            COUNT(DISTINCT t.id) as task_count,
                            COUNT(DISTINCT n.id) as note_count,
                            COUNT(DISTINCT ct.tag_id) as tag_count,
                            SUM(o.value) as total_opportunity_value,
                            c.created_at,
                            c.updated_at
                        FROM keap.contacts c
                        LEFT JOIN keap.companies co ON c.company_id = co.id
                        LEFT JOIN keap.users u ON c.owner_id = u.id
                        LEFT JOIN keap.opportunities o ON c.id = o.contact_id
                        LEFT JOIN keap.tasks t ON c.id = t.contact_id
                        LEFT JOIN keap.notes n ON c.id = n.contact_id
                        LEFT JOIN keap.contact_tags ct ON c.id = ct.contact_id
                        GROUP BY c.id, c.given_name, c.family_name, c.email, 
                                c.email_status, c.email_opted_in, c.score_value,
                                co.name, co.website, u.email, c.created_at, c.updated_at
                    )
                    SELECT * FROM contact_metrics
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cur.execute(query)
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                data = [dict(zip(columns, row)) for row in rows]
                
                if not data:
                    print("No analytics data found")
                    return None
                
                # Convert to DataFrame
                df = pd.DataFrame(data)
                
                # Export to Parquet
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"analytics_dataset_{timestamp}.parquet"
                filepath = self.output_dir / filename
                
                df.to_parquet(filepath, index=False, engine='pyarrow')
                
                print(f"Exported {len(data)} analytics records to {filepath}")
                return str(filepath)
        finally:
            conn.close()

class ExportManager:
    """Manages data exports with multiple formats and options."""
    
    def __init__(self, cfg: Settings, output_dir: str = "exports"):
        self.cfg = cfg
        self.csv_exporter = CSVExporter(cfg, output_dir)
        self.parquet_exporter = ParquetExporter(cfg, output_dir)
        self.output_dir = Path(output_dir)
    
    def export_entity(self, entity: str, format: str = "csv", 
                     where_clause: str = None, limit: int = None) -> str:
        """Export a specific entity in the specified format."""
        if format.lower() == "csv":
            return self.csv_exporter.export_table(entity, where_clause=where_clause, limit=limit)
        elif format.lower() == "parquet":
            return self.parquet_exporter.export_table(entity, where_clause=where_clause, limit=limit)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_all(self, format: str = "csv", where_clause: str = None, 
                  limit: int = None) -> List[str]:
        """Export all entities in the specified format."""
        if format.lower() == "csv":
            return self.csv_exporter.export_all_entities(where_clause=where_clause, limit=limit)
        elif format.lower() == "parquet":
            return self.parquet_exporter.export_all_entities(where_clause=where_clause, limit=limit)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_analytics(self, format: str = "parquet", limit: int = None) -> str:
        """Export analytics dataset."""
        if format.lower() == "parquet":
            return self.parquet_exporter.export_analytics_dataset(limit=limit)
        elif format.lower() == "csv":
            return self.csv_exporter.export_contacts_with_relationships(limit=limit)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def list_exported_files(self) -> List[str]:
        """List all exported files in the output directory."""
        return [str(f) for f in self.output_dir.glob("*") if f.is_file()]
    
    def cleanup_old_exports(self, days: int = 30):
        """Clean up export files older than specified days."""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        removed_count = 0
        
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_date:
                file_path.unlink()
                removed_count += 1
        
        print(f"Removed {removed_count} old export files")
