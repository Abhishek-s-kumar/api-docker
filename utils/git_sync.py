"""
Git synchronization utilities
"""
import os
from pathlib import Path
import yaml

# Load config
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

REPO_PATH = Path(config['git']['repo_path'])

def get_rules_list(subdir="rules"):
    """Get list of files in a directory"""
    target_path = REPO_PATH / subdir
    if not target_path.exists():
        return []
    
    return [f.name for f in target_path.glob("*.xml")]

def clone_or_pull():
    """Mock git sync - returns success"""
    return {
        "success": True,
        "message": "Repository available",
        "path": str(REPO_PATH),
        "exists": REPO_PATH.exists()
    }
