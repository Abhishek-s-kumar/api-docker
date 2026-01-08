#!/usr/bin/env python3
"""
Safe test of Wazuh API Puller - no actual deployment
"""
import requests
import json
import tempfile
import zipfile
import os
from pathlib import Path

# Configuration from test_deployment.json
config = {
    "api_url": "http://localhost:8000",
    "api_key": "wazuh_test_key",
    "server_id": "test-wazuh-01"
}

headers = {
    "Authorization": f"Bearer {config['api_key']}",
    "User-Agent": f"Test-Puller/{config['server_id']}"
}

def test_connection():
    """Test API connection"""
    try:
        response = requests.get(
            f"{config['api_url']}/health",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ API Connection: {response.json()['status']}")
            return True
        else:
            print(f"❌ API Connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Connection error: {e}")
        return False

def get_rules_info():
    """Get rules information"""
    try:
        response = requests.get(
            f"{config['api_url']}/api/rules/list",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rules Info: {data['counts']['rules']} rules, {data['counts']['decoders']} decoders")
            return data
        else:
            print(f"❌ Failed to get rules info: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Rules info error: {e}")
        return None

def download_and_inspect():
    """Download package and inspect contents"""
    try:
        print(f"Downloading rules package from {config['api_url']}...")
        
        response = requests.get(
            f"{config['api_url']}/api/rules/package",
            headers=headers,
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                temp_path = f.name
            
            file_size = os.path.getsize(temp_path)
            print(f"✅ Downloaded: {file_size:,} bytes")
            
            # Inspect contents
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                files = zip_ref.namelist()
                print(f"📦 Package contains {len(files)} files:")
                for file in files:
                    print(f"  - {file}")
            
            # Cleanup
            os.unlink(temp_path)
            return True
        else:
            print(f"❌ Download failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False

def main():
    print(f"\n{'='*60}")
    print(f"SAFE API PULLER TEST - {config['server_id']}")
    print(f"{'='*60}")
    
    # Test connection
    if not test_connection():
        return False
    
    # Get rules info
    rules_info = get_rules_info()
    if not rules_info:
        return False
    
    # Download and inspect
    if not download_and_inspect():
        return False
    
    print(f"\n{'='*60}")
    print("✅ TEST COMPLETE - API is working correctly!")
    print(f"{'='*60}")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
