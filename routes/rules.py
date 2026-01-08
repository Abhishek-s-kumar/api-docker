"""
Rules API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sqlite3
from datetime import datetime
from pathlib import Path
import yaml
import tempfile
import zipfile
import os

router = APIRouter()
security = HTTPBearer()

# Load config
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

REPO_PATH = Path(config['git']['repo_path'])

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

@router.get("/list")
async def list_rules(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List available rules"""
    api_key = credentials.credentials
    
    # Verify API key
    server_info = verify_api_key(api_key)
    
    # Get rules from repository
    rules = []
    decoders = []
    
    rules_path = REPO_PATH / "rules"
    decoders_path = REPO_PATH / "decoders"
    
    if rules_path.exists():
        for xml_file in rules_path.glob("*.xml"):
            rules.append(xml_file.name)
    
    if decoders_path.exists():
        for xml_file in decoders_path.glob("*.xml"):
            decoders.append(xml_file.name)
    
    # Update server last seen
    conn = sqlite3.connect('deployments.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE servers SET last_seen = ? WHERE server_id = ?
    """, (datetime.now().isoformat(), server_info['server_id']))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "server": server_info['server_id'],
        "rules": sorted(rules),
        "decoders": sorted(decoders),
        "counts": {
            "rules": len(rules),
            "decoders": len(decoders),
            "total": len(rules) + len(decoders)
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/package")
async def download_package(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Download all rules as zip package"""
    api_key = credentials.credentials
    
    # Verify API key
    server_info = verify_api_key(api_key)
    
    # Create temp zip file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_file.name, 'w') as zipf:
        # Add rules
        rules_path = REPO_PATH / "rules"
        if rules_path.exists():
            for xml_file in rules_path.glob("*.xml"):
                zipf.write(xml_file, f"rules/{xml_file.name}")
        
        # Add decoders
        decoders_path = REPO_PATH / "decoders"
        if decoders_path.exists():
            for xml_file in decoders_path.glob("*.xml"):
                zipf.write(xml_file, f"decoders/{xml_file.name}")
    
    # Log the download
    conn = sqlite3.connect('deployments.db')
    cursor = conn.cursor()
    
    # Count files
    rules_count = len(list(rules_path.glob("*.xml"))) if rules_path.exists() else 0
    decoders_count = len(list(decoders_path.glob("*.xml"))) if decoders_path.exists() else 0
    
    cursor.execute("""
        INSERT INTO deployments (server_id, timestamp, success, file_count)
        VALUES (?, ?, 1, ?)
    """, (server_info['server_id'], datetime.now().isoformat(), rules_count + decoders_count))
    
    conn.commit()
    conn.close()
    
    return FileResponse(
        path=temp_file.name,
        filename=f"wazuh-rules-{datetime.now().strftime('%Y%m%d')}.zip",
        media_type="application/zip"
    )

@router.get("/stats")
async def get_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get repository statistics"""
    api_key = credentials.credentials
    server_info = verify_api_key(api_key)
    
    rules_path = REPO_PATH / "rules"
    decoders_path = REPO_PATH / "decoders"
    
    rules_count = len(list(rules_path.glob("*.xml"))) if rules_path.exists() else 0
    decoders_count = len(list(decoders_path.glob("*.xml"))) if decoders_path.exists() else 0
    
    return {
        "server": server_info['server_id'],
        "repository": str(REPO_PATH),
        "file_counts": {
            "rules": rules_count,
            "decoders": decoders_count,
            "total": rules_count + decoders_count
        },
        "last_checked": datetime.now().isoformat()
    }
