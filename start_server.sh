#!/bin/bash
# Start script for Wazuh API Server

# Activate virtual environment
source venv/bin/activate

# Check if database exists
if [ ! -f deployments.db ]; then
    echo "Initializing database..."
    python3 -c "from models import init_db; init_db()"
fi

# Check if log file exists
if [ ! -f server.log ]; then
    touch server.log
    chmod 666 server.log
fi

# Start the server
echo "Starting Wazuh API Server..."
echo "Server will be available at: http://0.0.0.0:8000"
echo "Press Ctrl+C to stop"

python3 app.py
