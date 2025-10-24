#!/usr/bin/env python3
"""
Unit tests for the database module.
"""

import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import pytest
import psycopg2
from datetime import datetime

# Add the src directory to the path
import sys
sys.path.insert(0, '/opt/es-keap-database/src')

from keap_export.db import (
    get_conn, 
    upsert, 
    upsert_user, 
    upsert_contact, 
    upsert_company, 
    upsert_tag,
    upsert_opportunity,
    upsert_task,
    upsert_note,
    upsert_product,
    upsert_order,
    to_jsonb
)
from keap_export.config import Settings


class TestGetConn:
    """Test the get_conn function."""
    
    def test_get_conn_success(self):
        """Test successful database connection."""
        cfg = Settings(
            db_host="localhost",
            db_port=5432,
            db_name="test_db",
            db_user="test_user",
            db_password="test_password"
        )
        
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            
            conn = get_conn(cfg)
            
            assert conn == mock_conn
            mock_connect.assert_called_once_with(
                host="localhost",
                port=5432,
                database="test_db",
                user="test_user",
                password="test_password"
            )
    
    def test_get_conn_connection_error(self):
        """Test database connection error."""
        cfg = Settings(
            db_host="invalid_host",
            db_port=5432,
            db_name="test_db",
            db_user="test_user",
            db_password="test_password"
        )
        
        with patch('psycopg2.connect') as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError("Connection failed")
            
            with pytest.raises(psycopg2.OperationalError):
                get_conn(cfg)


class TestToJsonb:
    """Test the to_jsonb function."""
    
    def test_to_jsonb_simple_dict(self):
        """Test converting simple dict to JSONB."""
        data = {"key": "value", "number": 123}
        result = to_jsonb(data)
        
        assert isinstance(result, psycopg2.extras.Json)
        assert result.adapted == data
    
    def test_to_jsonb_with_datetime(self):
        """Test converting dict with datetime to JSONB."""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        data = {"key": "value", "created_at": dt}
        result = to_jsonb(data)
        
        assert isinstance(result, psycopg2.extras.Json)
        # The datetime should be converted to ISO format
        assert "created_at" in result.adapted
        assert result.adapted["created_at"] == "2023-01-01T12:00:00"
    
    def test_to_jsonb_nested_datetime(self):
        """Test converting nested dict with datetime to JSONB."""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        data = {
            "user": {
                "id": 1,
                "created_at": dt
            }
        }
        result = to_jsonb(data)
        
        assert isinstance(result, psycopg2.extras.Json)
        assert result.adapted["user"]["created_at"] == "2023-01-01T12:00:00"
    
    def test_to_jsonb_list_with_datetime(self):
        """Test converting list with datetime to JSONB."""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        data = [{"id": 1, "created_at": dt}, {"id": 2, "created_at": dt}]
        result = to_jsonb(data)
        
        assert isinstance(result, psycopg2.extras.Json)
        assert len(result.adapted) == 2
        assert result.adapted[0]["created_at"] == "2023-01-01T12:00:00"


class TestUpsertUser:
    """Test the upsert_user function."""
    
    def test_upsert_user_success(self):
        """Test successful user upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        user_data = {
            'id': 123,
            'given_name': 'John',
            'family_name': 'Doe',
            'email_address': 'john@example.com',
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 123, 'name': 'John Doe'}
        }
        
        upsert_user(mock_conn, user_data)
        
        # Verify cursor.execute was called
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        # Check that the SQL contains the expected fields
        sql = call_args[0][0]
        assert "INSERT INTO keap.users" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "given_name" in sql
        assert "family_name" in sql
        assert "email_address" in sql
    
    def test_upsert_user_with_none_values(self):
        """Test user upsert with None values."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        user_data = {
            'id': 123,
            'given_name': None,
            'family_name': None,
            'email_address': 'john@example.com',
            'created_at': None,
            'updated_at': None,
            'raw': {'id': 123}
        }
        
        upsert_user(mock_conn, user_data)
        
        mock_cursor.execute.assert_called_once()


class TestUpsertContact:
    """Test the upsert_contact function."""
    
    def test_upsert_contact_success(self):
        """Test successful contact upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        contact_data = {
            'id': 456,
            'given_name': 'Jane',
            'family_name': 'Smith',
            'email_address': 'jane@example.com',
            'company_id': 789,
            'owner_id': 123,
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 456, 'name': 'Jane Smith'}
        }
        
        upsert_contact(mock_conn, contact_data)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        sql = call_args[0][0]
        assert "INSERT INTO keap.contacts" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "company_id" in sql
        assert "owner_id" in sql


class TestUpsertCompany:
    """Test the upsert_company function."""
    
    def test_upsert_company_success(self):
        """Test successful company upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        company_data = {
            'id': 789,
            'name': 'Test Company',
            'website': 'https://example.com',
            'phone': '555-1234',
            'address': '123 Main St',
            'city': 'Anytown',
            'state': 'CA',
            'postal_code': '12345',
            'country_code': 'US',
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 789, 'name': 'Test Company'}
        }
        
        upsert_company(mock_conn, company_data)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        sql = call_args[0][0]
        assert "INSERT INTO keap.companies" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "website" in sql
        assert "phone" in sql
    
    def test_upsert_company_with_datetime_conversion(self):
        """Test company upsert with datetime conversion."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        company_data = {
            'id': 789,
            'name': 'Test Company',
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 789}
        }
        
        upsert_company(mock_conn, company_data)
        
        # Verify the datetime objects were converted to strings
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]
        assert params['created_at'] == '2023-01-01T12:00:00'
        assert params['updated_at'] == '2023-01-02T12:00:00'


class TestUpsertTag:
    """Test the upsert_tag function."""
    
    def test_upsert_tag_success(self):
        """Test successful tag upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        tag_data = {
            'id': 101,
            'name': 'VIP Customer',
            'category_id': 1,
            'category_name': 'Customer Type',
            'description': 'High-value customer',
            'raw': {'id': 101, 'name': 'VIP Customer'}
        }
        
        upsert_tag(mock_conn, tag_data)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        sql = call_args[0][0]
        assert "INSERT INTO keap.tags" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "category_id" in sql
        assert "category_name" in sql


class TestUpsertOpportunity:
    """Test the upsert_opportunity function."""
    
    def test_upsert_opportunity_success(self):
        """Test successful opportunity upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        opportunity_data = {
            'id': 201,
            'contact_id': 456,
            'company_id': 789,
            'name': 'Big Deal',
            'stage_id': 1,
            'pipeline_id': 1,
            'value': 10000.50,
            'owner_id': 123,
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 201, 'name': 'Big Deal'}
        }
        
        upsert_opportunity(mock_conn, opportunity_data)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        sql = call_args[0][0]
        assert "INSERT INTO keap.opportunities" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "stage_id" in sql
        assert "pipeline_id" in sql
        assert "value" in sql


class TestUpsertTask:
    """Test the upsert_task function."""
    
    def test_upsert_task_success(self):
        """Test successful task upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        task_data = {
            'id': 301,
            'contact_id': 456,
            'company_id': 789,
            'opportunity_id': 201,
            'title': 'Follow up call',
            'description': 'Call the client about the proposal',
            'type': 'Call',
            'priority': 'High',
            'status': 'Pending',
            'due_date': datetime(2023, 1, 15, 14, 0, 0),
            'completed_date': None,
            'owner_id': 123,
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 301, 'title': 'Follow up call'}
        }
        
        upsert_task(mock_conn, task_data)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        sql = call_args[0][0]
        assert "INSERT INTO keap.tasks" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "completed_date" in sql


class TestUpsertNote:
    """Test the upsert_note function."""
    
    def test_upsert_note_success(self):
        """Test successful note upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        note_data = {
            'id': 401,
            'contact_id': 456,
            'company_id': 789,
            'opportunity_id': 201,
            'title': 'Meeting notes',
            'body': 'Discussed pricing and timeline',
            'type': 'Note',
            'owner_id': 123,
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 401, 'title': 'Meeting notes'}
        }
        
        upsert_note(mock_conn, note_data)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        sql = call_args[0][0]
        assert "INSERT INTO keap.notes" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "body" in sql


class TestUpsertProduct:
    """Test the upsert_product function."""
    
    def test_upsert_product_success(self):
        """Test successful product upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        product_data = {
            'id': 501,
            'name': 'Premium Service',
            'description': 'High-end service package',
            'price': 999.99,
            'sku': 'PREMIUM-001',
            'active': True,
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 501, 'name': 'Premium Service'}
        }
        
        upsert_product(mock_conn, product_data)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        sql = call_args[0][0]
        assert "INSERT INTO keap.products" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "sku" in sql
        assert "active" in sql


class TestUpsertOrder:
    """Test the upsert_order function."""
    
    def test_upsert_order_success(self):
        """Test successful order upsert."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        order_data = {
            'id': 601,
            'contact_id': 456,
            'company_id': 789,
            'order_number': 'ORD-001',
            'order_date': datetime(2023, 1, 1, 12, 0, 0),
            'order_total': 1999.98,
            'order_status': 'Completed',
            'payment_status': 'Paid',
            'created_at': datetime(2023, 1, 1, 12, 0, 0),
            'updated_at': datetime(2023, 1, 2, 12, 0, 0),
            'raw': {'id': 601, 'order_number': 'ORD-001'}
        }
        
        upsert_order(mock_conn, order_data)
        
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        
        sql = call_args[0][0]
        assert "INSERT INTO keap.orders" in sql
        assert "ON CONFLICT (id) DO UPDATE" in sql
        assert "order_number" in sql
        assert "order_total" in sql


class TestUpsertDispatcher:
    """Test the upsert dispatcher function."""
    
    def test_upsert_dispatcher_users(self):
        """Test upsert dispatcher for users."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        user_data = {
            'id': 123,
            'given_name': 'John',
            'family_name': 'Doe',
            'email_address': 'john@example.com',
            'raw': {'id': 123}
        }
        
        with patch('keap_export.db.upsert_user') as mock_upsert_user:
            upsert(mock_conn, 'users', user_data)
            mock_upsert_user.assert_called_once_with(mock_conn, user_data)
    
    def test_upsert_dispatcher_contacts(self):
        """Test upsert dispatcher for contacts."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        contact_data = {
            'id': 456,
            'given_name': 'Jane',
            'family_name': 'Smith',
            'email_address': 'jane@example.com',
            'raw': {'id': 456}
        }
        
        with patch('keap_export.db.upsert_contact') as mock_upsert_contact:
            upsert(mock_conn, 'contacts', contact_data)
            mock_upsert_contact.assert_called_once_with(mock_conn, contact_data)
    
    def test_upsert_dispatcher_unknown_entity(self):
        """Test upsert dispatcher for unknown entity."""
        mock_conn = Mock()
        
        data = {'id': 123, 'name': 'Test'}
        
        with pytest.raises(ValueError, match="Unknown entity: unknown"):
            upsert(mock_conn, 'unknown', data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

