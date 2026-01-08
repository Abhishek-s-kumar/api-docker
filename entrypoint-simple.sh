#!/bin/bash
set -e

echo "=== Starting Wazuh API Server ==="
echo "Time: $(date)"

# Create necessary directories
mkdir -p /data /logs /git-repo

# Create a minimal config if not exists
if [ ! -f config.yaml ]; then
    cat > config.yaml << 'CONFIG_EOF'
server:
  host: "0.0.0.0"
  port: 8000
  reload: false
database:
  path: "/data/deployments.db"
logging:
  level: "INFO"
  file: "/logs/wazuh-api.log"
CONFIG_EOF
fi

# Initialize database with a simpler approach
if [ ! -f "/data/deployments.db" ]; then
    echo "Initializing database..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('/data/deployments.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS servers (id INTEGER PRIMARY KEY, server_id TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS api_keys (id INTEGER PRIMARY KEY, key TEXT)')
conn.commit()
conn.close()
print('Database initialized')
"
fi

# Start the server
echo "Starting server..."
exec python3 -c "
from wazuh import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"
