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
                       since: Optional[str] = None, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Fetch all pages of data from the API endpoint."""
        all_records = []
        page = 0
        limit = 1000
        
        # Add since parameter if provided
        if since:
            params = params or {}
            params['since'] = since
        
        self.logger.log_sync_start(self.entity, since, dry_run)
        start_time = time.time()
        
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
                
                # Log request to ETL tracker
                self.etl_tracker.log_request(
                    endpoint=self.endpoint,
                    page_offset=page * limit,
                    page_limit=limit,
                    http_status=200,
                    item_count=len(records),
                    duration_ms=int(page_duration)
                )
                
                all_records.extend(records)
                
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
        
        duration = time.time() - start_time
        self.logger.log_sync_end(self.entity, len(all_records), duration, success=True)
        
        return all_records
    
    def _extract_records(self, data: Any) -> List[Dict[str, Any]]:
        """Extract records from API response. Override in subclasses if needed."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try common response formats
            for key in ['contacts', 'items', 'data', 'results']:
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []
    
    def _handle_throttle_headers(self):
        """Handle throttle headers from the last response."""
        # This would be implemented in the client to check headers
        # For now, just a small delay
        time.sleep(0.1)
    
    def sync_entity(self, since: Optional[str] = None, dry_run: bool = False) -> int:
        """Sync all records for this entity."""
        try:
            # Fetch all records
            raw_records = self.fetch_all_pages(since=since, dry_run=dry_run)
            
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
            self.etl_tracker.record_source_count(self.entity, processed_count)
            
            return processed_count
            
        except Exception as e:
            self.logger.log_error(self.entity, f"Sync failed: {e}")
            raise

class ContactSync(BaseSync):
    """Sync contacts from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'contacts', '/crm/rest/v1/contacts')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform contact record for database."""
        return {
            'id': raw_record.get('id'),
            'company_id': raw_record.get('company_id'),
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
            'created_at': self._parse_datetime(raw_record.get('date_created')),
            'updated_at': self._parse_datetime(raw_record.get('date_modified')),
            'raw': to_jsonb(raw_record)
        }

class CompanySync(BaseSync):
    """Sync companies from Keap API."""
    
    def __init__(self, cfg: Settings):
        super().__init__(cfg, 'companies', '/crm/rest/v1/companies')
    
    def transform_record(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform company record for database."""
        return {
            'id': raw_record.get('id'),
            'name': raw_record.get('company_name'),
            'website': raw_record.get('website'),
            'phone': raw_record.get('phone_number'),
            'address': raw_record.get('address', {}).get('line1'),
            'city': raw_record.get('address', {}).get('locality'),
            'state': raw_record.get('address', {}).get('region'),
            'postal_code': raw_record.get('address', {}).get('postal_code'),
            'country_code': raw_record.get('address', {}).get('country_code'),
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

# Factory function to create sync instances
def create_sync(cfg: Settings, entity: str) -> BaseSync:
    """Create a sync instance for the specified entity."""
    sync_classes = {
        'contacts': ContactSync,
        'companies': CompanySync,
        'tags': TagSync,
        # Add more as they're implemented
    }
    
    if entity not in sync_classes:
        raise ValueError(f"Unknown entity: {entity}")
    
    return sync_classes[entity](cfg)
