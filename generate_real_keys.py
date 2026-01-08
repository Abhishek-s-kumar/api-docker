#!/usr/bin/env python3
import secrets
import sqlite3
import hashlib
from datetime import datetime
import sys

def generate_server_key(server_id, description=""):
    """Generate and register a real API key"""
    # Generate secure key
    api_key = f"wazuh_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Connect to database
    conn = sqlite3.connect('deployments.db')
    cursor = conn.cursor()
    
    try:
        # Add to api_keys table
        cursor.execute("""
            INSERT INTO api_keys (key, key_hash, server_id, is_admin, active, created_at)
            VALUES (?, ?, ?, 0, 1, ?)
        """, (api_key, key_hash, server_id, datetime.now().isoformat()))
        
        # Add to servers table
        cursor.execute("""
            INSERT OR REPLACE INTO servers (server_id, description, first_seen, last_seen, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (server_id, description, datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        
        print(f"\n✅ GENERATED REAL API KEY")
        print(f"Server ID: {server_id}")
        print(f"Description: {description}")
        print(f"API Key: {api_key}")
        print(f"API URL: http://YOUR_SERVER_IP:8000")
        print(f"\n⚠️  SAVE THIS KEY - It won't be shown again!")
        
        return api_key
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate_real_keys.py <server_id> [description]")
        sys.exit(1)
    
    server_id = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else ""
    generate_server_key(server_id, description)
