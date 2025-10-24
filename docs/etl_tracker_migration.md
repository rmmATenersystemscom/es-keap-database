# ETL Tracker Migration Guide

This guide explains the migration from the old ETL tracker to the new simplified, more reliable implementation.

## Overview

The new ETL tracker (v2) provides:

- **Simplified API**: Fewer methods, clearer purpose
- **Better Error Handling**: Graceful degradation on failures
- **Context Manager**: Automatic cleanup and error handling
- **Thread Safety**: Stateless operations for better concurrency
- **Performance**: Optimized database operations
- **Reliability**: Robust error handling and recovery

## Key Differences

### Old ETL Tracker (etl_meta.py)

**Issues:**
- Complex state management with persistent connections
- Mixed responsibilities (run tracking + detailed metrics)
- Error-prone connection handling
- Difficult to use in concurrent scenarios
- Hard to test and debug

**API:**
```python
tracker = get_etl_tracker(cfg)
run_id = tracker.start_run('My sync')
tracker.log_request(endpoint, offset, limit, status, count, duration)
tracker.end_run(True, 'Completed')
```

### New ETL Tracker (etl_tracker_v2.py)

**Benefits:**
- Stateless operations with fresh connections
- Clear separation of concerns
- Context manager for automatic cleanup
- Better error handling and logging
- Thread-safe design
- Easier to test and maintain

**API Options:**

**Option 1 - Direct Usage:**
```python
tracker = SimpleETLTracker(cfg)
run_id = tracker.start_run('My sync')
tracker.log_request(run_id, endpoint, offset, limit, status, count, duration)
tracker.end_run(run_id, True, 'Completed')
```

**Option 2 - Context Manager:**
```python
with ETLRunContext(tracker, 'My sync') as run:
    run.log_request(endpoint, offset, limit, status, count, duration)
    # Automatic cleanup on exit
```

## Migration Steps

### 1. Update Imports

**Old:**
```python
from keap_export.etl_meta import get_etl_tracker
```

**New:**
```python
from keap_export.etl_tracker_v2 import SimpleETLTracker, ETLRunContext
```

### 2. Update Tracker Creation

**Old:**
```python
tracker = get_etl_tracker(cfg)
```

**New:**
```python
tracker = SimpleETLTracker(cfg)
```

### 3. Update Run Management

**Old (Stateful):**
```python
run_id = tracker.start_run('My sync')
# tracker.run_id is automatically set
tracker.log_request(endpoint, offset, limit, status, count, duration)
tracker.end_run(True, 'Completed')
```

**New (Explicit):**
```python
run_id = tracker.start_run('My sync')
tracker.log_request(run_id, endpoint, offset, limit, status, count, duration)
tracker.end_run(run_id, True, 'Completed')
```

**Or with Context Manager:**
```python
with ETLRunContext(tracker, 'My sync') as run:
    run.log_request(endpoint, offset, limit, status, count, duration)
    # Automatic cleanup
```

### 4. Update Error Handling

**Old:**
```python
try:
    tracker.log_request(endpoint, offset, limit, status, count, duration)
except Exception as e:
    # Handle error
```

**New:**
```python
success = tracker.log_request(run_id, endpoint, offset, limit, status, count, duration)
if not success:
    print("Warning: Failed to log request")
```

## API Comparison

### Core Methods

| Old Method | New Method | Changes |
|------------|------------|---------|
| `start_run(notes)` | `start_run(notes)` | Returns run_id explicitly |
| `end_run(success, notes)` | `end_run(run_id, success, notes)` | Requires run_id parameter |
| `log_request(...)` | `log_request(run_id, ...)` | Requires run_id parameter |
| `log_source_count(entity, count)` | `log_source_count(run_id, entity, count)` | Requires run_id parameter |

### New Methods

| Method | Purpose |
|--------|---------|
| `get_run_metrics(run_id)` | Get metrics for a specific run |
| `get_recent_runs(limit)` | Get recent ETL runs |
| `cleanup_old_runs(days)` | Clean up old runs |
| `is_enabled()` | Check if tracking is enabled |
| `disable()` / `enable()` | Control tracking state |

### Context Manager

```python
# Automatic run management
with ETLRunContext(tracker, 'My sync') as run:
    run.log_request(endpoint, offset, limit, status, count, duration)
    run.log_source_count('contacts', 1000)
    # Automatic cleanup on exit (success or failure)
```

## Migration Examples

### Example 1: Basic Sync Script

**Old:**
```python
def sync_contacts(cfg):
    tracker = get_etl_tracker(cfg)
    run_id = tracker.start_run('Contact sync')
    
    try:
        # Sync logic
        for page in fetch_pages():
            tracker.log_request('/contacts', page.offset, page.limit, 200, len(page.items), page.duration)
        
        tracker.end_run(True, 'Sync completed')
    except Exception as e:
        tracker.end_run(False, f'Error: {e}')
```

**New (Direct):**
```python
def sync_contacts(cfg):
    tracker = SimpleETLTracker(cfg)
    run_id = tracker.start_run('Contact sync')
    
    try:
        # Sync logic
        for page in fetch_pages():
            tracker.log_request(run_id, '/contacts', page.offset, page.limit, 200, len(page.items), page.duration)
        
        tracker.end_run(run_id, True, 'Sync completed')
    except Exception as e:
        tracker.end_run(run_id, False, f'Error: {e}')
```

**New (Context Manager):**
```python
def sync_contacts(cfg):
    tracker = SimpleETLTracker(cfg)
    
    with ETLRunContext(tracker, 'Contact sync') as run:
        # Sync logic
        for page in fetch_pages():
            run.log_request('/contacts', page.offset, page.limit, 200, len(page.items), page.duration)
        # Automatic cleanup
```

### Example 2: Complex Sync with Multiple Entities

**Old:**
```python
def sync_all_entities(cfg):
    tracker = get_etl_tracker(cfg)
    run_id = tracker.start_run('Full sync')
    
    try:
        for entity in ['contacts', 'companies', 'opportunities']:
            # Sync entity
            tracker.log_source_count(entity, count)
        
        tracker.end_run(True, 'All entities synced')
    except Exception as e:
        tracker.end_run(False, f'Error: {e}')
```

**New:**
```python
def sync_all_entities(cfg):
    tracker = SimpleETLTracker(cfg)
    
    with ETLRunContext(tracker, 'Full sync') as run:
        for entity in ['contacts', 'companies', 'opportunities']:
            # Sync entity
            run.log_source_count(entity, count)
        # Automatic cleanup
```

## Benefits of Migration

### 1. Reliability
- **Fresh Connections**: Each operation gets a fresh database connection
- **Error Isolation**: Failures in one operation don't affect others
- **Automatic Cleanup**: Context manager ensures proper cleanup

### 2. Performance
- **No Persistent Connections**: Reduces connection pool pressure
- **Stateless Operations**: Better for concurrent usage
- **Optimized Queries**: Simplified database operations

### 3. Maintainability
- **Clear API**: Fewer methods with clear purposes
- **Better Testing**: Easier to unit test individual operations
- **Error Handling**: Graceful degradation on failures

### 4. Usability
- **Context Manager**: Automatic run management
- **Explicit Parameters**: Clear what each method needs
- **Better Logging**: Improved error messages and warnings

## Backward Compatibility

The old ETL tracker (`etl_meta.py`) will continue to work, but new code should use the new tracker. The migration can be done gradually:

1. **Phase 1**: Use new tracker for new features
2. **Phase 2**: Migrate existing scripts one by one
3. **Phase 3**: Remove old tracker (future)

## Testing the Migration

```python
# Test script to verify migration
from keap_export.etl_tracker_v2 import SimpleETLTracker, ETLRunContext

def test_migration():
    tracker = SimpleETLTracker(cfg)
    
    # Test direct usage
    run_id = tracker.start_run('Migration test')
    tracker.log_request(run_id, '/test', 0, 100, 200, 50, 1000)
    tracker.end_run(run_id, True, 'Test completed')
    
    # Test context manager
    with ETLRunContext(tracker, 'Context test') as run:
        run.log_request('/test', 0, 100, 200, 25, 500)
    
    # Test metrics
    metrics = tracker.get_run_metrics(run_id)
    print(f"Metrics: {metrics}")
```

## Conclusion

The new ETL tracker provides a more reliable, maintainable, and user-friendly approach to ETL tracking. The migration is straightforward and provides significant benefits in terms of reliability, performance, and maintainability.

**Key Takeaways:**
- Use `SimpleETLTracker` for direct control
- Use `ETLRunContext` for automatic management
- All methods now require explicit `run_id` parameters
- Better error handling with return values
- Context manager provides automatic cleanup

---

**Version**: v1.0.2  
**Last Updated**: October 24, 2025 02:44 UTC  
**Maintainer**: Keap Database Team
