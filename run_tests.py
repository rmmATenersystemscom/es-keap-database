#!/usr/bin/env python3
"""
Test runner for Keap Export project.
"""

import sys
import os
import subprocess

def run_tests():
    """Run all unit tests."""
    # Add the src directory to the path
    sys.path.insert(0, '/opt/es-keap-database/src')
    
    # Change to the project directory
    os.chdir('/opt/es-keap-database')
    
    # Run pytest with verbose output
    cmd = ['.venv/bin/python', '-m', 'pytest', 'tests/', '-v', '--tb=short']
    
    print("Running unit tests...")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 50)
        print("❌ Some tests failed!")
        return e.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())

