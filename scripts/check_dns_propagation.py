#!/usr/bin/env python3
"""
Check DNS propagation for keapdb.enersystems.com
"""

import subprocess
import time
import sys

def check_dns(domain: str, expected_ip: str) -> bool:
    """Check if DNS resolves to expected IP."""
    try:
        result = subprocess.run(['nslookup', domain], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout
            if expected_ip in output:
                print(f"✅ {domain} resolves to {expected_ip}")
                return True
            else:
                print(f"⚠️  {domain} resolves but not to {expected_ip}")
                print(f"Output: {output}")
                return False
        else:
            print(f"❌ {domain} does not resolve yet")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout checking {domain}")
        return False
    except Exception as e:
        print(f"❌ Error checking {domain}: {e}")
        return False

def main():
    """Monitor DNS propagation."""
    domain = "keapdb.enersystems.com"
    expected_ip = "97.89.220.126"
    
    print(f"🌐 Monitoring DNS propagation for {domain}")
    print(f"Expected IP: {expected_ip}")
    print("=" * 60)
    
    max_attempts = 12  # Check for up to 1 hour (5 min intervals)
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\nAttempt {attempt}/{max_attempts} - {time.strftime('%H:%M:%S')}")
        
        if check_dns(domain, expected_ip):
            print(f"\n🎉 DNS propagation successful!")
            print(f"   {domain} -> {expected_ip}")
            return 0
        
        if attempt < max_attempts:
            print("⏳ Waiting 5 minutes before next check...")
            time.sleep(300)  # Wait 5 minutes
    
    print(f"\n⚠️  DNS propagation not complete after {max_attempts} attempts")
    print("This is normal - DNS propagation can take up to 24 hours")
    print("You can manually check with: nslookup keapdb.enersystems.com")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
