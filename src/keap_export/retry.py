from __future__ import annotations
import time
import random
import requests
from typing import Callable, Any, Optional, Dict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import Settings

class KeapRetryHandler:
    """Enhanced retry handler with exponential backoff and jitter for Keap API calls."""
    
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.max_retries = getattr(cfg, 'max_retries', 5)
        self.retry_delay = getattr(cfg, 'retry_delay', 1)
        self.max_retry_delay = getattr(cfg, 'max_retry_delay', 30)
    
    def is_retryable_error(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry."""
        if isinstance(exception, requests.exceptions.RequestException):
            if hasattr(exception, 'response') and exception.response is not None:
                status_code = exception.response.status_code
                # Retry on 429 (throttle), 5xx (server errors), and network issues
                return status_code in [429, 500, 502, 503, 504] or status_code >= 500
            # Network errors (timeout, connection, etc.)
            return True
        return False
    
    def get_retry_delay(self, attempt: int, base_delay: float = None) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        if base_delay is None:
            base_delay = self.retry_delay
        
        # Exponential backoff: delay = base_delay * (2 ^ attempt)
        delay = base_delay * (2 ** attempt)
        
        # Cap at max_retry_delay
        delay = min(delay, self.max_retry_delay)
        
        # Add jitter (±25% random variation)
        jitter = random.uniform(0.75, 1.25)
        delay = delay * jitter
        
        return delay
    
    def get_throttle_delay(self, response: requests.Response) -> Optional[float]:
        """Extract throttle delay from response headers."""
        # Check for Retry-After header
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        
        # Check for Keap-specific throttle headers
        throttle_available = response.headers.get('x-keap-product-throttle-available')
        if throttle_available:
            try:
                available = int(throttle_available)
                if available < 10:  # Very low throttle budget
                    return 60.0  # Wait 1 minute
                elif available < 50:  # Low throttle budget
                    return 10.0  # Wait 10 seconds
            except ValueError:
                pass
        
        return None
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if we should retry based on exception and attempt count."""
        if attempt >= self.max_retries:
            return False
        
        if not self.is_retryable_error(exception):
            return False
        
        # For throttle errors, always retry (up to max attempts)
        if isinstance(exception, requests.exceptions.RequestException):
            if hasattr(exception, 'response') and exception.response is not None:
                if exception.response.status_code == 429:
                    return True
        
        return True
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic and exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    break
                
                # Calculate delay
                delay = self.get_retry_delay(attempt)
                
                # Check for throttle-specific delay
                if isinstance(e, requests.exceptions.RequestException):
                    if hasattr(e, 'response') and e.response is not None:
                        throttle_delay = self.get_throttle_delay(e.response)
                        if throttle_delay:
                            delay = throttle_delay
                
                # Log retry attempt
                print(f"Retry attempt {attempt + 1}/{self.max_retries + 1} after {delay:.2f}s delay: {e}")
                
                # Wait before retry
                time.sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception

def retry_on_throttle(max_attempts: int = 5, base_delay: float = 1.0, max_delay: float = 30.0):
    """Decorator for retrying on throttle and server errors."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_handler = KeapRetryHandler(type('Config', (), {
                'max_retries': max_attempts - 1,
                'retry_delay': base_delay,
                'max_retry_delay': max_delay
            })())
            
            return retry_handler.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator

def handle_keap_response(response: requests.Response) -> requests.Response:
    """Handle Keap API response with throttle awareness."""
    # Check for throttle headers
    throttle_available = response.headers.get('x-keap-product-throttle-available')
    if throttle_available:
        try:
            available = int(throttle_available)
            if available < 50:  # Low throttle budget
                print(f"Warning: Low throttle budget remaining: {available}")
        except ValueError:
            pass
    
    # Check for tenant throttle
    tenant_throttle = response.headers.get('x-keap-tenant-throttle-available')
    if tenant_throttle:
        try:
            available = int(tenant_throttle)
            if available < 10:  # Very low tenant throttle
                print(f"Warning: Low tenant throttle budget remaining: {available}")
        except ValueError:
            pass
    
    # Raise for status if not successful
    response.raise_for_status()
    return response

def create_retry_session(cfg: Settings) -> requests.Session:
    """Create a requests session with retry configuration."""
    session = requests.Session()
    
    # Set up retry adapter
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    retry_strategy = Retry(
        total=cfg.max_retries,
        backoff_factor=cfg.retry_delay,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
