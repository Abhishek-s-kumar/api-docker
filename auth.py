"""
Authentication module
"""
import sqlite3
from fastapi import HTTPException

def verify_api_key(api_key: str) -> dict:
    """Verify API key against database"""
    if not api_key:
        raise HTTPException(status_code=401, detail="No API key provided")
    
    conn = sqlite3.connect('deployments.db')
    cursor = conn.cursor()
    
    # Check if key exists and is active
    cursor.execute("""
        SELECT key, server_id, is_admin 
        FROM api_keys 
        WHERE key = ? AND active = 1
    """, (api_key,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    return {
        "key": result[0],
        "server_id": result[1],
        "is_admin": bool(result[2])
    }

def is_admin(api_key: str) -> bool:
    """Check if API key has admin privileges"""
    try:
        info = verify_api_key(api_key)
        return info.get('is_admin', False)
    except:
        return False
