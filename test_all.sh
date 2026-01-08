#!/bin/bash
echo "=== COMPLETE WAZUH API TEST ==="
echo "Timestamp: $(date)"
echo ""

cd /opt/wazuh-api

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if server is running
echo "1. Checking if server is running..."
if pgrep -f "uvicorn" > /dev/null; then
    echo "   ✅ Server is running"
    SERVER_PID=$(pgrep -f "uvicorn")
else
    echo "   ⚠️  Starting server..."
    uvicorn app:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &
    SERVER_PID=$!
    sleep 5
fi

echo "2. Testing basic connectivity..."
curl -s http://localhost:8000/health
echo ""

echo "3. Testing root endpoint..."
curl -s http://localhost:8000/
echo ""

echo "4. Checking database..."
sqlite3 deployments.db "SELECT COUNT(*) as total_servers FROM servers;"
sqlite3 deployments.db "SELECT server_id, last_seen FROM servers;"

echo "5. Testing with API key..."
API_KEY=$(sqlite3 deployments.db "SELECT key FROM api_keys LIMIT 1;")
echo "Using API key: ${API_KEY:0:20}..."

echo "6. Testing rules list..."
curl -H "Authorization: Bearer $API_KEY" \
     -s http://localhost:8000/api/rules/list | python3 -m json.tool | head -20

echo "7. Testing package download..."
curl -H "Authorization: Bearer $API_KEY" \
     http://localhost:8000/api/rules/package -o /tmp/test.zip 2>/dev/null

if [ -f /tmp/test.zip ]; then
    echo "   ✅ Download successful"
    ls -lh /tmp/test.zip
else
    echo "   ❌ Download failed"
fi

echo "8. Checking repository..."
ls -la /opt/wazuh-rules-repo/
find /opt/wazuh-rules-repo/ -name "*.xml" | wc -l

echo ""
echo "=== TEST COMPLETE ==="
