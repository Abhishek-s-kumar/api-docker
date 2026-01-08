#!/usr/bin/env python3
import secrets
import sqlite3
from datetime import datetime
import socket

def generate_key(server_id, description=""):
    """Generate a production API key"""
    api_key = f"wazuh_prod_{secrets.token_urlsafe(32)}"
    
    conn = sqlite3.connect('deployments.db')
    cursor = conn.cursor()
    
    # Add server if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO servers (server_id, description, first_seen, last_seen, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (server_id, description, datetime.now().isoformat(), datetime.now().isoformat()))
    
    # Add API key
    cursor.execute("""
        INSERT INTO api_keys (key, server_id, is_admin, active, created_at)
        VALUES (?, ?, 0, 1, ?)
    """, (api_key, server_id, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return api_key

# Get server IP for display
def get_server_ip():
    """Get server IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "YOUR_SERVER_IP"

# Generate keys for your servers
servers = [
    ("wazuh-prod-01", "Primary Production Server"),
    ("wazuh-prod-02", "Secondary Production Server"),
    ("wazuh-staging-01", "Staging Environment"),
    ("wazuh-monitoring-01", "Monitoring Server"),
]

server_ip = get_server_ip()

print("=== GENERATING PRODUCTION API KEYS ===")
print("SAVE THESE KEYS SECURELY - THEY WON'T BE SHOWN AGAIN")
print("=" * 70)

for server_id, description in servers:
    key = generate_key(server_id, description)
    print(f"\n🔑 {server_id}")
    print(f"   📝 {description}")
    print(f"   🔐 {key}")
    print(f"   🌐 API URL: http://{server_ip}:8000")
    print("-" * 70)

print("\n✅ Keys generated and saved to database")
print("\nTo test a key:")
print('curl -H "Authorization: Bearer YOUR_KEY_HERE" http://localhost:8000/api/rules/stats')
