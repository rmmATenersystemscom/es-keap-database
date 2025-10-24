from __future__ import annotations
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from .config import Settings
from .client import KeapClient
from .db import get_conn, upsert, to_jsonb
from .logger import get_logger
from .etl_meta import get_etl_tracker
from .retry import KeapRetryHandler

class BaseSync:
    """Base class for all Keap entity sync operations."""
    
    def __init__(self, cfg: Settings, entity: str, endpoint: str):
        self.cfg = cfg
        self.entity = entity
        self.endpoint = endpoint
        self.client = KeapClient(cfg)
        self.logger = get_logger(cfg)
        self.etl_tracker = get_etl_tracker(cfg)
        self.retry_handler = KeapRetryHandler(cfg)
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw API record to database format. Override in subclasses."""
        return {
            'id': raw_record.get('id'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from Keap API."""
        if not dt_str:
            return None
        try:
            # Keap typically uses ISO format
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def fetch_all_pages(self, params: Optional[Dict[str, Any]] = None, 
                       since: Optional[str] = None, dry_run: bool = False, etl_tracker=None) -> List[Dict[str, Any]]:
        """Fetch all pages of data from the API endpoint."""
        all_records = []
        page = 0
        limit = 1000
        
        # Check for resume checkpoint
        if etl_tracker:
            checkpoint = etl_tracker.get_last_checkpoint(self.entity, 'page')
            if checkpoint:
                page = checkpoint.get('last_page', 0)
                limit = checkpoint.get('page_limit', 1000)
                self.logger.log_info(f"Resuming {self.entity} sync from page {page}")
        
        # Note: Keap API doesn't support date filtering, so we'll filter client-side
        # Don't add since parameter to API call
        
        self.logger.log_sync_start(self.entity, since, dry_run)
        start_time = time.time()
        
        # Update sync progress to running
        if etl_tracker:
            etl_tracker.update_sync_progress(self.entity, 'running', page)
        
        try:
            while True:
                page_start = time.time()
                page_params = (params or {}).copy()
                page_params.update({'limit': limit, 'offset': page * limit})
                
                # Make API request with retry logic
                def make_request():
                    response = self.client.request('GET', self.endpoint, params=page_params)
                    return response.json()
                
                try:
                    data = self.retry_handler.retry_with_backoff(make_request)
                except Exception as e:
                    self.logger.log_error(self.entity, f"Failed to fetch page {page}: {e}")
                    raise
                
                # Extract records from response
                records = self._extract_records(data)
                if not records:
                    break
                
                # Log page fetch
                page_duration = (time.time() - page_start) * 1000
                self.logger.log_page_fetch(self.entity, page, len(records), int(page_duration))
                
                # Log request to ETL tracker (use external tracker if provided)
                tracker = etl_tracker if etl_tracker is not None else self.etl_tracker
                
                # Basic request logging
                tracker.log_request(
                    endpoint=self.endpoint,
                    page_offset=page * limit,
                    page_limit=limit,
                    http_status=200,
                    item_count=len(records),
                    duration_ms=int(page_duration)
                )
                
                # Detailed metrics logging
                tracker.log_detailed_request(
                    entity=self.entity,
                    endpoint=self.endpoint,
                    page_offset=page * limit,
                    page_limit=limit,
                    http_status=200,
                    item_count=len(records),
                    duration_ms=int(page_duration),
                    throttle_remaining=getattr(self.client, 'last_throttle_remaining', None),
                    throttle_type=getattr(self.client, 'last_throttle_type', None),
                    retry_count=getattr(self.client, 'last_retry_count', 0),
                    response_size_bytes=getattr(self.client, 'last_response_size', None)
                )
                
                all_records.extend(records)
                
                # Save checkpoint for resume capability
                if etl_tracker:
                    checkpoint_data = {
                        'last_page': page,
                        'page_limit': limit,
                        'total_records': len(all_records),
                        'last_page_records': len(records)
                    }
                    etl_tracker.save_checkpoint(self.entity, 'page', checkpoint_data)
                    etl_tracker.update_sync_progress(self.entity, 'running', page, len(all_records))
                
                # In dry run mode, only fetch first page
                if dry_run:
                    self.logger.log_info(f"Dry run: Only fetching first page ({len(records)} records)")
                    break
                
                # Check if we got fewer records than requested (last page)
                if len(records) < limit:
                    break
                
                page += 1
                
                # Respect throttle headers
                self._handle_throttle_headers()
        
        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_sync_end(self.entity, len(all_records), duration, success=False, error=str(e))
            raise
        
        # Apply client-side date filtering if since parameter provided
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                filtered_records = []
                for record in all_records:
                    # Check both date_created and date_modified fields
                    created_at = self._parse_datetime(record.get('date_created'))
                    updated_at = self._parse_datetime(record.get('date_modified'))
                    
                    # Include record if either created or updated since the given date
                    if (created_at and created_at >= since_dt) or (updated_at and updated_at >= since_dt):
                        filtered_records.append(record)
                
                self.logger.log_info(f"Date filtering: {len(all_records)} -> {len(filtered_records)} records (since {since})")
                all_records = filtered_records
            except ValueError as e:
                self.logger.log_error(self.entity, f"Invalid since date format: {since}. Error: {e}")
                # Continue with all records if date parsing fails
        
        duration = time.time() - start_time
        self.logger.log_sync_end(self.entity, len(all_records), duration, success=True)
        
        return all_records
    
    def _extract_records(self, data: Any) -> List[Dict[str, Any]]:
        """Extract records from API response. Override in subclasses if needed."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try common response formats
            for key in ['contacts', 'users', 'tags', 'companies', 'opportunities', 'tasks', 'notes', 'products', 'orders', 'items', 'data', 'results']:
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []
    
    def _handle_throttle_headers(self):
        """Handle throttle headers from the last response."""
        # The throttle handling is now implemented in the client
        # This method is kept for backward compatibility but does nothing
        # as the client handles throttling automatically
        pass
    
    def sync_entity(self, since: Optional[str] = None, dry_run: bool = False, etl_tracker=None) -> int:
        """Sync all records for this entity."""
        # Use external tracker if provided, otherwise use instance tracker
        tracker = etl_tracker if etl_tracker is not None else self.etl_tracker
        
        try:
            # Fetch all records
            raw_records = self.fetch_all_pages(since=since, dry_run=dry_run, etl_tracker=tracker)
            
            if dry_run:
                self.logger.log_info(f"Dry run: Would process {len(raw_records)} {self.entity} records")
                return len(raw_records)
            
            # Transform and upsert records
            processed_count = 0
            batch_size = 100
            
            for i in range(0, len(raw_records), batch_size):
                batch = raw_records[i:i + batch_size]
                batch_start = time.time()
                
                # Transform batch
                transformed_batch = []
                for raw_record in batch:
                    try:
                        transformed = self.transform_record(raw_record)
                        if transformed:
                            transformed_batch.append(transformed)
                    except Exception as e:
                        self.logger.log_error(self.entity, f"Failed to transform record: {e}", 
                                            context={'record_id': raw_record.get('id')})
                        continue
                
                # Upsert batch
                if transformed_batch:
                    conn = get_conn(self.cfg)
                    try:
                        for record in transformed_batch:
                            upsert(conn, self.entity, record)
                        conn.commit()
                        
                        batch_duration = (time.time() - batch_start) * 1000
                        self.logger.log_upsert_batch(self.entity, len(transformed_batch), int(batch_duration))
                        processed_count += len(transformed_batch)
                        
                    except Exception as e:
                        conn.rollback()
                        self.logger.log_error(self.entity, f"Failed to upsert batch: {e}")
                        raise
                    finally:
                        conn.close()
            
            # Record source count
            tracker.record_source_count(self.entity, processed_count)
            
            # Mark entity as completed
            if etl_tracker:
                etl_tracker.update_sync_progress(self.entity, 'completed', items_processed=processed_count)
            
            return processed_count
            
        except Exception as e:
            self.logger.log_error(self.entity, f"Sync failed: {e}")
            
            # Mark entity as failed
            if etl_tracker:
                etl_tracker.update_sync_progress(self.entity, 'failed', error_msg=str(e))
            
            raise

class UserSync(BaseSync):
    """Sync users from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'users', '/crm/rest/v1/users')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform user record for database."""
        return {
            'id': raw_record.get('id'),
            'email': raw_record.get('email_address'),
            'given_name': raw_record.get('given_name'),
            'family_name': raw_record.get('family_name'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('last_updated')),
            'raw': to_jsonb(raw_record)
        }

class PipelineSync(BaseSync):
    """Sync pipelines from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'pipelines', '/crm/rest/v1/pipelines')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform pipeline record for database."""
        return {
            'id': raw_record.get('id'),
            'name': raw_record.get('name'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class StageSync(BaseSync):
    """Sync stages from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'stages', '/crm/rest/v1/stages')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform stage record for database."""
        return {
            'id': raw_record.get('id'),
            'pipeline_id': raw_record.get('pipeline_id'),
            'name': raw_record.get('name'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class ContactSync(BaseSync):
    """Sync contacts from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'contacts', '/crm/rest/v1/contacts')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform contact record for database."""
        return {
            'id': raw_record.get('id'),
            'company_id': raw_record.get('company', {}).get('id') if isinstance(raw_record.get('company'), dict) else raw_record.get('company_id'),
            'given_name': raw_record.get('given_name'),
            'family_name': raw_record.get('family_name'),
            'email': raw_record.get('email_addresses', [{}])[0].get('email') if raw_record.get('email_addresses') else None,
            'phone': raw_record.get('phone_numbers', [{}])[0].get('number') if raw_record.get('phone_numbers') else None,
            'address': raw_record.get('addresses', [{}])[0].get('line1') if raw_record.get('addresses') else None,
            'city': raw_record.get('addresses', [{}])[0].get('locality') if raw_record.get('addresses') else None,
            'state': raw_record.get('addresses', [{}])[0].get('region') if raw_record.get('addresses') else None,
            'postal_code': raw_record.get('addresses', [{}])[0].get('postal_code') if raw_record.get('addresses') else None,
            'country_code': raw_record.get('addresses', [{}])[0].get('country_code') if raw_record.get('addresses') else None,
            'owner_id': raw_record.get('owner_id'),
            # Custom fields
            'middle_name': raw_record.get('middle_name'),
            'email_status': raw_record.get('email_status'),
            'email_opted_in': raw_record.get('email_opted_in'),
            'score_value': raw_record.get('ScoreValue'),
            'tag_ids': to_jsonb(raw_record.get('tag_ids', [])),
            'email_addresses': to_jsonb(raw_record.get('email_addresses', [])),
            'phone_numbers': to_jsonb(raw_record.get('phone_numbers', [])),
            'addresses': to_jsonb(raw_record.get('addresses', [])),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('last_updated')),
            'raw': to_jsonb(raw_record)
        }

class CompanySync(BaseSync):
    """Sync companies from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'companies', '/crm/rest/v1/companies')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform company record for database."""
        # Extract phone number from dict if present
        phone = raw_record.get('phone_number')
        if isinstance(phone, dict):
            phone = phone.get('number')
        
        return {
            'id': raw_record.get('id'),
            'name': raw_record.get('company_name'),
            'website': raw_record.get('website'),
            'phone': phone,
            'address': raw_record.get('address', {}).get('line1'),
            'city': raw_record.get('address', {}).get('locality'),
            'state': raw_record.get('address', {}).get('region'),
            'postal_code': raw_record.get('address', {}).get('postal_code'),
            'country_code': raw_record.get('address', {}).get('country_code'),
            # Custom fields
            'phone_numbers': to_jsonb(raw_record.get('phone_numbers', [])),
            'addresses': to_jsonb(raw_record.get('addresses', [])),
            'custom_fields': to_jsonb(raw_record.get('custom_fields', {})),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class TagSync(BaseSync):
    """Sync tags from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'tags', '/crm/rest/v1/tags')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform tag record for database."""
        return {
            'id': raw_record.get('id'),
            'name': raw_record.get('name'),
            'description': raw_record.get('description'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class ContactTagSync(BaseSync):
    """Sync contact tags from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'contact_tags', '/crm/rest/v1/contacts/{contact_id}/tags')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform contact tag record for database."""
        return {
            'contact_id': raw_record.get('contact_id'),
            'tag_id': raw_record.get('tag_id'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class OpportunitySync(BaseSync):
    """Sync opportunities from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'opportunities', '/crm/rest/v1/opportunities')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform opportunity record for database."""
        return {
            'id': raw_record.get('id'),
            'contact_id': raw_record.get('contact_id'),
            'company_id': raw_record.get('company_id'),
            'pipeline_id': raw_record.get('pipeline_id'),
            'stage_id': raw_record.get('stage_id'),
            'name': raw_record.get('name'),
            'description': raw_record.get('description'),
            'value': raw_record.get('value'),
            'currency': raw_record.get('currency'),
            'status': raw_record.get('status'),
            'owner_id': raw_record.get('owner_id'),
            # Custom fields
            'custom_fields': to_jsonb(raw_record.get('custom_fields', {})),
            'stage_moves': to_jsonb(raw_record.get('stage_moves', [])),
            'notes': to_jsonb(raw_record.get('notes', [])),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class TaskSync(BaseSync):
    """Sync tasks from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'tasks', '/crm/rest/v1/tasks')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform task record for database."""
        return {
            'id': raw_record.get('id'),
            'contact_id': raw_record.get('contact_id'),
            'company_id': raw_record.get('company_id'),
            'opportunity_id': raw_record.get('opportunity_id'),
            'title': raw_record.get('title'),
            'description': raw_record.get('description'),
            'type': raw_record.get('type'),
            'priority': raw_record.get('priority'),
            'status': raw_record.get('status'),
            'due_date': self._parse_datetime(raw_record.get('due_date')),
            'completed_date': self._parse_datetime(raw_record.get('completed_date')),
            'owner_id': raw_record.get('owner_id'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class NoteSync(BaseSync):
    """Sync notes from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'notes', '/crm/rest/v1/notes')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform note record for database."""
        return {
            'id': raw_record.get('id'),
            'contact_id': raw_record.get('contact_id'),
            'company_id': raw_record.get('company_id'),
            'opportunity_id': raw_record.get('opportunity_id'),
            'title': raw_record.get('title'),
            'body': raw_record.get('body'),
            'type': raw_record.get('type'),
            'owner_id': raw_record.get('owner_id'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class ProductSync(BaseSync):
    """Sync products from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'products', '/crm/rest/v1/products')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform product record for database."""
        return {
            'id': raw_record.get('id'),
            'name': raw_record.get('name'),
            'description': raw_record.get('description'),
            'sku': raw_record.get('sku'),
            'price': raw_record.get('price'),
            'currency': raw_record.get('currency'),
            'status': raw_record.get('status'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class OrderSync(BaseSync):
    """Sync orders from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'orders', '/crm/rest/v1/orders')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform order record for database."""
        return {
            'id': raw_record.get('id'),
            'contact_id': raw_record.get('contact_id'),
            'company_id': raw_record.get('company_id'),
            'order_number': raw_record.get('order_number'),
            'status': raw_record.get('status'),
            'total': raw_record.get('total'),
            'currency': raw_record.get('currency'),
            'shipping_address': raw_record.get('shipping_address'),
            'billing_address': raw_record.get('billing_address'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class OrderItemSync(BaseSync):
    """Sync order items from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'order_items', '/crm/rest/v1/orders/{order_id}/items')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform order item record for database."""
        return {
            'id': raw_record.get('id'),
            'order_id': raw_record.get('order_id'),
            'product_id': raw_record.get('product_id'),
            'quantity': raw_record.get('quantity'),
            'price': raw_record.get('price'),
            'total': raw_record.get('total'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class PaymentSync(BaseSync):
    """Sync payments from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'payments', '/crm/rest/v1/payments')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform payment record for database."""
        return {
            'id': raw_record.get('id'),
            'order_id': raw_record.get('order_id'),
            'amount': raw_record.get('amount'),
            'currency': raw_record.get('currency'),
            'status': raw_record.get('status'),
            'payment_method': raw_record.get('payment_method'),
            'transaction_id': raw_record.get('transaction_id'),
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

# Define sync order: reference tables first, then main entities
SYNC_ORDER = [
    # Reference tables (no dependencies)
    'users',
    'pipelines', 
    'stages',
    'tags',
    
    # Main entities (depend on reference tables)
    'companies',
    'contacts',
    'contact_tags',
    'opportunities',
    'tasks',
    'notes',
    'products',
    'orders',
    'order_items',
    'payments',
]

# Factory function to create sync instances
def create_sync(cfg: Settings, entity: str) -> BaseSync:
    """Create a sync instance for the specified entity."""
    sync_classes = {
        'users': UserSync,
        'pipelines': PipelineSync,
        'stages': StageSync,
        'contacts': ContactSync,
        'companies': CompanySync,
        'tags': TagSync,
        'contact_tags': ContactTagSync,
        'opportunities': OpportunitySync,
        'tasks': TaskSync,
        'notes': NoteSync,
        'products': ProductSync,
        'orders': OrderSync,
        'order_items': OrderItemSync,
        'payments': PaymentSync,
    }
    
    if entity not in sync_classes:
        raise ValueError(f"Unknown entity: {entity}")
    
    return sync_classes[entity](cfg)
