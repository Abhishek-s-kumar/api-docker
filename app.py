from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import sqlite3
import os

app = FastAPI(
    title="Wazuh Rules API",
    description="Centralized API for Wazuh rules distribution",
    version="1.0.0"
)

security = HTTPBearer()

def verify_api_key(api_key: str) -> dict:
    """Simple API key verification"""
    conn = sqlite3.connect('deployments.db')
    cursor = conn.cursor()
    cursor.execute("SELECT key, server_id FROM api_keys WHERE key = ? AND active = 1", (api_key,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {"key": result[0], "server_id": result[1]}

@app.get("/")
async def root():
    return {
        "service": "Wazuh Rules API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/health",
            "/api/rules/list",
            "/api/rules/package",
            "/api/rules/stats"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = sqlite3.connect('deployments.db')
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Import and include routes
from routes import rules
app.include_router(rules.router, prefix="/api/rules", tags=["rules"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
