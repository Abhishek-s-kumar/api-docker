#!/usr/bin/env python3
"""
Simple Admin Dashboard for Wazuh Rules API
"""
import sqlite3
from datetime import datetime
import json

def get_stats():
    """Get database statistics"""
    conn = sqlite3.connect('deployments.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Server statistics
    cursor.execute("SELECT COUNT(*) as total_servers FROM servers")
    total_servers = cursor.fetchone()['total_servers']
    
    cursor.execute("SELECT COUNT(*) as active_servers FROM servers WHERE is_active = 1")
    active_servers = cursor.fetchone()['active_servers']
    
    cursor.execute("SELECT COUNT(*) as total_keys FROM api_keys WHERE active = 1")
    total_keys = cursor.fetchone()['total_keys']
    
    # Deployment statistics
    cursor.execute("SELECT COUNT(*) as total_deployments FROM deployments")
    total_deployments = cursor.fetchone()['total_deployments']
    
    cursor.execute("SELECT COUNT(*) as successful_deployments FROM deployments WHERE success = 1")
    successful_deployments = cursor.fetchone()['successful_deployments']
    
    # Recent deployments
    cursor.execute("""
        SELECT server_id, timestamp, success, file_count
        FROM deployments 
        ORDER BY timestamp DESC 
        LIMIT 5
    """)
    recent = [dict(row) for row in cursor.fetchall()]
    
    # Server list
    cursor.execute("""
        SELECT server_id, description, last_seen, is_active
        FROM servers 
        ORDER BY last_seen DESC
    """)
    servers = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "generated": datetime.now().isoformat(),
        "servers": {
            "total": total_servers,
            "active": active_servers,
            "api_keys": total_keys
        },
        "deployments": {
            "total": total_deployments,
            "successful": successful_deployments,
            "failed": total_deployments - successful_deployments,
            "success_rate": (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0
        },
        "recent_deployments": recent,
        "server_list": servers
    }

def print_dashboard():
    """Print a simple dashboard"""
    stats = get_stats()
    
    print("=" * 60)
    print("WAZUH RULES API - ADMIN DASHBOARD")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Server stats
    print("SERVER STATISTICS")
    print("-" * 40)
    print(f"Total Servers: {stats['servers']['total']}")
    print(f"Active Servers: {stats['servers']['active']}")
    print(f"Active API Keys: {stats['servers']['api_keys']}")
    print()
    
    # Deployment stats
    print("DEPLOYMENT STATISTICS")
    print("-" * 40)
    print(f"Total Deployments: {stats['deployments']['total']}")
    print(f"Successful: {stats['deployments']['successful']}")
    print(f"Failed: {stats['deployments']['failed']}")
    print(f"Success Rate: {stats['deployments']['success_rate']:.1f}%")
    print()
    
    # Recent deployments
    if stats['recent_deployments']:
        print("RECENT DEPLOYMENTS")
        print("-" * 40)
        for dep in stats['recent_deployments']:
            status = "✅" if dep['success'] else "❌"
            print(f"{status} {dep['server_id']} - {dep['file_count']} files - {dep['timestamp'][:19]}")
        print()
    
    # Server list
    if stats['server_list']:
        print("REGISTERED SERVERS")
        print("-" * 40)
        for server in stats['server_list']:
            status = "ACTIVE" if server['is_active'] else "INACTIVE"
            last_seen = server['last_seen'][:19] if server['last_seen'] else "Never"
            print(f"{server['server_id']:20} {status:10} Last: {last_seen}")
    
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    if args.json:
        stats = get_stats()
        print(json.dumps(stats, indent=2))
    else:
        print_dashboard()
