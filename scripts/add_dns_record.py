#!/usr/bin/env python3
"""
Add DNS A record to GoDaddy using API credentials.
"""

import requests
import json
import sys
from typing import Dict, Any

# GoDaddy API credentials (from the secure storage)
GODADDY_API_KEY = "9ZfdEaudbRz_WQjxNA9QQbkBY98Uugrzn6"
GODADDY_API_SECRET = "UfQrKGfaet97vgGos2UpGF"

# GoDaddy API base URL
GODADDY_BASE_URL = "https://api.godaddy.com/v1"

def add_a_record(domain: str, subdomain: str, ip_address: str) -> bool:
    """Add an A record to GoDaddy DNS."""
    
    # Prepare headers
    headers = {
        'Authorization': f'sso-key {GODADDY_API_KEY}:{GODADDY_API_SECRET}',
        'Content-Type': 'application/json'
    }
    
    # First, get existing records
    url = f"{GODADDY_BASE_URL}/domains/{domain}/records/A/{subdomain}"
    
    try:
        print(f"Getting existing A records for {subdomain}.{domain}...")
        get_response = requests.get(url, headers=headers)
        
        existing_records = []
        if get_response.status_code == 200:
            existing_records = get_response.json()
            print(f"Found {len(existing_records)} existing A records")
        elif get_response.status_code == 404:
            print("No existing A records found (this is normal for new subdomain)")
        else:
            print(f"Warning: Could not get existing records. Status: {get_response.status_code}")
        
        # Add the new record to the list
        new_record = {
            'type': 'A',
            'name': subdomain,
            'data': ip_address,
            'ttl': 3600  # 1 hour TTL
        }
        
        # Check if record already exists
        for record in existing_records:
            if record.get('data') == ip_address:
                print(f"✅ A record already exists: {subdomain}.{domain} -> {ip_address}")
                return True
        
        # Add the new record
        existing_records.append(new_record)
        
        print(f"Adding A record: {subdomain}.{domain} -> {ip_address}")
        print(f"Using GoDaddy API: {url}")
        
        # Make the API request to replace all A records for this subdomain
        response = requests.put(url, headers=headers, json=existing_records)
        
        if response.status_code == 200:
            print("✅ A record added successfully!")
            return True
        else:
            print(f"❌ Failed to add A record. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding A record: {e}")
        return False

def get_current_records(domain: str) -> None:
    """Get current DNS records for the domain."""
    
    headers = {
        'Authorization': f'sso-key {GODADDY_API_KEY}:{GODADDY_API_SECRET}',
        'Content-Type': 'application/json'
    }
    
    url = f"{GODADDY_BASE_URL}/domains/{domain}/records"
    
    try:
        print(f"\nCurrent DNS records for {domain}:")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            records = response.json()
            for record in records:
                if record.get('type') == 'A':
                    print(f"  {record.get('name', '@')}.{domain} -> {record.get('data')} (TTL: {record.get('ttl')})")
        else:
            print(f"❌ Failed to get records. Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting records: {e}")

def main():
    """Main function."""
    domain = "enersystems.com"
    subdomain = "keapdb"
    ip_address = "97.89.220.126"
    
    print("🌐 GoDaddy DNS Record Management")
    print("=" * 50)
    
    # Show current records
    get_current_records(domain)
    
    # Add the A record
    print(f"\nAdding A record for {subdomain}.{domain}...")
    success = add_a_record(domain, subdomain, ip_address)
    
    if success:
        print(f"\n✅ Successfully added A record:")
        print(f"   {subdomain}.{domain} -> {ip_address}")
        print(f"\nDNS propagation may take up to 24 hours.")
        print(f"You can verify with: nslookup {subdomain}.{domain}")
    else:
        print(f"\n❌ Failed to add A record.")
        return 1
    
    # Show updated records
    print(f"\nUpdated DNS records:")
    get_current_records(domain)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
