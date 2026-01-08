#!/bin/bash
set -e

echo "=== Starting Wazuh API Server ==="
echo "Time: $(date)"
echo "Python: $(python3 --version)"
echo ""

# Generate config.yaml from environment variables
echo "Generating configuration..."
cat > config.yaml << CONFIG_EOF
server:
  host: "0.0.0.0"
  port: 8000
  reload: false

git:
  repo_url: "${GIT_REPO_URL:-https://github.com/Abhishek-s-kumar/prox-wazuh-ci.git }"
  repo_path: "${GIT_REPO_PATH:-/git-repo}"
  sync_interval: 300
  branch: "${GIT_BRANCH:-main}"

auth:
  secret_key: "${SECRET_KEY:-changeme-in-production-please-change}"
  token_expiry: 1440
  require_https: false

database:
  path: "${DATABASE_PATH:-/data/deployments.db}"

rate_limit:
  enabled: true
  requests_per_minute: 60

logging:
  level: "${LOG_LEVEL:-INFO}"
  file: "${LOG_PATH:-/logs/wazuh-api.log}"
CONFIG_EOF

echo "Configuration generated."

# Initialize database if not exists
if [ ! -f "${DATABASE_PATH:-/data/deployments.db}" ]; then
    echo "Initializing database..."
    python3 -c "
import sqlite3
import os

db_path = os.environ.get('DATABASE_PATH', '/data/deployments.db')
db_dir = os.path.dirname(db_path)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS servers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id TEXT UNIQUE NOT NULL,
        description TEXT,
        first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        server_id TEXT,
        is_admin INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (server_id) REFERENCES servers (server_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS deployments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        success INTEGER DEFAULT 0,
        file_count INTEGER DEFAULT 0,
        error_message TEXT,
        deployment_time REAL,
        FOREIGN KEY (server_id) REFERENCES servers (server_id)
    )
''')

conn.commit()

# Create test server and key for initial testing
import secrets
from datetime import datetime

test_key = 'wazuh_test_' + secrets.token_hex(16)
cursor.execute('''
    INSERT OR IGNORE INTO servers (server_id, description, first_seen, last_seen, is_active)
    VALUES (?, ?, ?, ?, 1)
''', ('test-server-01', 'Docker Test Server', datetime.now().isoformat(), datetime.now().isoformat()))

cursor.execute('''
    INSERT INTO api_keys (key, server_id, is_admin, active, created_at)
    VALUES (?, ?, 0, 1, ?)
''', (test_key, 'test-server-01', datetime.now().isoformat()))

conn.commit()
conn.close()

print(f'Database initialized at {db_path}')
print(f'Test API Key: {test_key}')
"
else
    echo "Database already exists at ${DATABASE_PATH:-/data/deployments.db}"
fi

# Clone Git repository if specified
if [ -n "$GIT_REPO_URL" ] && [ ! -d "/git-repo/.git" ]; then
    echo "Cloning Git repository: $GIT_REPO_URL"
    git clone "$GIT_REPO_URL" /git-repo
    echo "Repository cloned to /git-repo"
elif [ -d "/git-repo/.git" ]; then
    echo "Git repository already exists at /git-repo"
else
    echo "No Git repository configured. Using empty directory."
    mkdir -p /git-repo/rules /git-repo/decoders
fi

# Ensure log directory exists
mkdir -p /logs

# Start the server
echo ""
echo "Starting Wazuh API Server..."
echo "API URL: http://0.0.0.0:8000"
echo "Health: http://localhost:8000/health"
echo ""

# Choose server based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Running in PRODUCTION mode with gunicorn"
    exec gunicorn app:app \
        --workers ${WORKERS:-4} \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --access-logfile /logs/access.log \
        --error-logfile /logs/error.log \
        --log-level info
else
    echo "Running in DEVELOPMENT mode with uvicorn"
    exec uvicorn app:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level info
fi
