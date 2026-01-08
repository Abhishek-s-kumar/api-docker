"""
Database models for Wazuh Rules API
"""
import sqlite3
import os
import logging
from datetime import datetime
import yaml

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

DATABASE_PATH = config['database']['path']
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a database connection with proper error handling"""
    try:
        # Ensure directory exists
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        logger.info(f"Database connection established: {DATABASE_PATH}")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        # Try fallback location
        fallback_path = "/tmp/deployments.db"
        logger.info(f"Trying fallback database: {fallback_path}")
        conn = sqlite3.connect(fallback_path)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create deployments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            ruleset_version TEXT,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            file_count INTEGER,
            deployment_time REAL
        )
    ''')
    
    # Create servers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            server_id TEXT PRIMARY KEY,
            description TEXT,
            first_seen DATETIME,
            last_seen DATETIME,
            is_active BOOLEAN DEFAULT 1,
            contact_email TEXT,
            environment TEXT,
            location TEXT
        )
    ''')
    
    # Create api_keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            key_hash TEXT NOT NULL,
            server_id TEXT,
            is_admin BOOLEAN DEFAULT 0,
            created_at DATETIME,
            last_used DATETIME,
            active BOOLEAN DEFAULT 1,
            FOREIGN KEY (server_id) REFERENCES servers (server_id)
        )
    ''')
    
    # Create deployment_files table (for detailed tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deployment_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deployment_id INTEGER,
            filename TEXT NOT NULL,
            size_bytes INTEGER,
            action TEXT,  -- 'added', 'modified', 'deleted'
            FOREIGN KEY (deployment_id) REFERENCES deployments (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")
    
    # Verify the database file was created
    if os.path.exists(DATABASE_PATH):
        logger.info(f"Database file created at: {DATABASE_PATH}")
        # Set proper permissions
        os.chmod(DATABASE_PATH, 0o644)
    else:
        logger.warning(f"Database file not found at: {DATABASE_PATH}")

def record_deployment(server_id, success=True, ruleset_version=None, 
                     error_message=None, file_count=0, deployment_time=0.0):
    """Record a deployment in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO deployments 
        (server_id, timestamp, ruleset_version, success, error_message, file_count, deployment_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        server_id,
        datetime.now().isoformat(),
        ruleset_version,
        1 if success else 0,
        error_message,
        file_count,
        deployment_time
    ))
    
    # Update server's last_seen timestamp
    cursor.execute('''
        INSERT OR REPLACE INTO servers (server_id, last_seen, is_active)
        VALUES (?, ?, 1)
    ''', (server_id, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    logger.info(f"Deployment recorded for server: {server_id}, success: {success}")
