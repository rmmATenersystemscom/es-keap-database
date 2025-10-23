from __future__ import annotations
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from .config import Settings

class KeapLogger:
    """Structured JSON logger for Keap export operations."""
    
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.logger = logging.getLogger('keap_export')
        self.logger.setLevel(getattr(logging, cfg.log_level.upper(), logging.INFO))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        
        # Set formatter based on config
        if cfg.log_format.lower() == 'json':
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
        
        self.logger.addHandler(handler)
    
    def log_sync_start(self, entity: str, since: Optional[str] = None, dry_run: bool = False) -> None:
        """Log the start of a sync operation."""
        self.logger.info(json.dumps({
            'event': 'sync_start',
            'entity': entity,
            'since': since,
            'dry_run': dry_run,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    def log_sync_end(self, entity: str, total_items: int, duration_seconds: float, 
                    success: bool = True, error: Optional[str] = None) -> None:
        """Log the end of a sync operation."""
        self.logger.info(json.dumps({
            'event': 'sync_end',
            'entity': entity,
            'total_items': total_items,
            'duration_seconds': duration_seconds,
            'success': success,
            'error': error,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    def log_page_fetch(self, entity: str, page: int, items_count: int, 
                       duration_ms: int, throttle_remaining: Optional[int] = None) -> None:
        """Log a page fetch operation."""
        self.logger.info(json.dumps({
            'event': 'page_fetch',
            'entity': entity,
            'page': page,
            'items_count': items_count,
            'duration_ms': duration_ms,
            'throttle_remaining': throttle_remaining,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    def log_throttle_hit(self, entity: str, retry_after: int, throttle_type: str) -> None:
        """Log when throttle limits are hit."""
        self.logger.warning(json.dumps({
            'event': 'throttle_hit',
            'entity': entity,
            'retry_after': retry_after,
            'throttle_type': throttle_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    def log_retry(self, entity: str, attempt: int, max_attempts: int, 
                  error: str, delay_seconds: float) -> None:
        """Log a retry attempt."""
        self.logger.warning(json.dumps({
            'event': 'retry',
            'entity': entity,
            'attempt': attempt,
            'max_attempts': max_attempts,
            'error': error,
            'delay_seconds': delay_seconds,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    def log_upsert_batch(self, entity: str, batch_size: int, duration_ms: int) -> None:
        """Log a batch upsert operation."""
        self.logger.info(json.dumps({
            'event': 'upsert_batch',
            'entity': entity,
            'batch_size': batch_size,
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    def log_validation_start(self, entity: str) -> None:
        """Log the start of validation."""
        self.logger.info(json.dumps({
            'event': 'validation_start',
            'entity': entity,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    def log_validation_result(self, entity: str, orphans: int, warnings: int, 
                             errors: int, duration_seconds: float) -> None:
        """Log validation results."""
        self.logger.info(json.dumps({
            'event': 'validation_result',
            'entity': entity,
            'orphans': orphans,
            'warnings': warnings,
            'errors': errors,
            'duration_seconds': duration_seconds,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }))
    
    def log_error(self, entity: str, error: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error."""
        log_data = {
            'event': 'error',
            'entity': entity,
            'error': error,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        if context:
            log_data['context'] = context
        
        self.logger.error(json.dumps(log_data))
    
    def log_info(self, message: str, entity: Optional[str] = None, **kwargs) -> None:
        """Log an info message."""
        log_data = {
            'event': 'info',
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        if entity:
            log_data['entity'] = entity
        if kwargs:
            log_data.update(kwargs)
        
        self.logger.info(json.dumps(log_data))

class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logging."""
    
    def format(self, record):
        # If the record already contains JSON, return it as-is
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            try:
                json.loads(record.msg)
                return record.msg
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Otherwise, format as JSON
        return json.dumps({
            'level': record.levelname,
            'message': record.getMessage(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'logger': record.name
        })

def get_logger(cfg: Settings) -> KeapLogger:
    """Get a configured KeapLogger instance."""
    return KeapLogger(cfg)
