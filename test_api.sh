#!/bin/bash
echo "=== Testing Wazuh API ==="

# Stop any running server
pkill -f "uvicorn" 2>/dev/null

# Start server
cd /opt/wazuh-api
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload > /tmp/api_test.log 2>&1 &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait for server to start
sleep 3

echo -e "\n1. Testing health endpoint:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo -e "\n2. Testing root endpoint:"
curl -s http://localhost:8000/ | python3 -m json.tool

echo -e "\n3. Testing rules list with test key:"
curl -H "Authorization: Bearer wazuh_test_key" \
     -s http://localhost:8000/api/rules/list | python3 -m json.tool | head -20

echo -e "\n4. Testing package download:"
curl -H "Authorization: Bearer wazuh_test_key" \
     http://localhost:8000/api/rules/package -o /tmp/test_rules.zip 2>/dev/null

if [ -f /tmp/test_rules.zip ]; then
    echo "Downloaded: $(ls -lh /tmp/test_rules.zip | awk '{print $5}')"
    echo "Files in zip:"
    unzip -l /tmp/test_rules.zip | grep "\.xml" | wc -l
else
    echo "Download failed!"
fi

echo -e "\n5. Checking database:"
sqlite3 deployments.db "SELECT COUNT(*) as deployments FROM deployments;"
sqlite3 deployments.db "SELECT server_id, timestamp, file_count FROM deployments ORDER BY timestamp DESC LIMIT 3;"

echo -e "\n6. Testing admin dashboard:"
python3 admin_dashboard.py --json | python3 -m json.tool | head -30

# Stop server
kill $SERVER_PID 2>/dev/null
echo -e "\n=== Test complete ==="
echo "Server log: /tmp/api_test.log"
