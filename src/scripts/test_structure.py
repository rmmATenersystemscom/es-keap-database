#!/usr/bin/env python3
"""
Test script to verify the project structure and imports work correctly.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, '/opt/es-keap-database/src')

def test_imports():
    """Test that all modules can be imported."""
    try:
        from keap_export.config import Settings
        from keap_export.sync_base import create_sync, SYNC_ORDER
        from keap_export.logger import get_logger
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_sync_classes():
    """Test that all sync classes can be created."""
    try:
        from keap_export.config import Settings
        from keap_export.sync_base import create_sync
        
        cfg = Settings()
        
        # Test creating each sync class
        for entity in ['contacts', 'companies', 'tags', 'opportunities', 'tasks', 'notes', 'products', 'orders', 'payments']:
            sync = create_sync(cfg, entity)
            print(f"✅ {entity} sync class created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Sync class creation error: {e}")
        return False

def test_scripts():
    """Test that all scripts exist and are executable."""
    scripts_dir = '/opt/es-keap-database/src/scripts'
    required_scripts = [
        'sync_contacts.py',
        'sync_companies.py', 
        'sync_tags.py',
        'sync_opportunities.py',
        'sync_tasks.py',
        'sync_notes.py',
        'sync_products.py',
        'sync_orders.py',
        'sync_payments.py',
        'sync_all.py',
        'run_validation.py'
    ]
    
    for script in required_scripts:
        script_path = os.path.join(scripts_dir, script)
        if os.path.exists(script_path):
            if os.access(script_path, os.X_OK):
                print(f"✅ {script} exists and is executable")
            else:
                print(f"⚠️  {script} exists but is not executable")
        else:
            print(f"❌ {script} not found")
            return False
    
    return True

def main():
    """Run all tests."""
    print("Testing Keap Exporter Structure")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Sync Classes Test", test_sync_classes),
        ("Scripts Test", test_scripts)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n{'='*40}")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Structure is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
