#!/bin/bash
PROJECT_DIR="/opt/wazuh-api-docker"

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found in $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo "🚀 Testing Wazuh API"
echo "===================="
echo ""

# Get API key
echo "1. Getting API key..."
API_KEY=$(docker compose exec -T wazuh-api sqlite3 /data/deployments.db \
  "SELECT key FROM api_keys WHERE server_id = 'test-server-01' LIMIT 1;")

if [ -z "$API_KEY" ]; then
    echo "❌ Could not get API key"
    exit 1
fi

echo "✅ API Key: $API_KEY"
echo ""

# Test health
echo "2. Testing health endpoint..."
curl -s http://localhost:8002/health | python3 -m json.tool
echo ""

# Get all endpoints
echo "3. Available endpoints:"
ENDPOINTS=$(curl -s http://localhost:8002/openapi.json | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for path in sorted(data['paths'].keys()):
        methods = ', '.join([m.upper() for m in data['paths'][path].keys()])
        print(f'  {methods:20s} {path}')
except Exception as e:
    print(f'Error: {e}')
")

if [ -z "$ENDPOINTS" ]; then
    echo "❌ Could not fetch endpoints"
else
    echo "$ENDPOINTS"
fi
echo ""

# Test common endpoints
echo "4. Testing endpoints with API key:"

# Try each common endpoint
for endpoint in "/api/v1/servers" "/api/v1/rules" "/deploy" "/auth/login"; do
    echo "   Testing: GET $endpoint"
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -H "X-API-Key: $API_KEY" http://localhost:8002$endpoint)
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | grep -v "HTTP_STATUS:")
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "   ✅ Success (200)"
    elif [ "$HTTP_STATUS" = "404" ]; then
        echo "   ❌ Not Found (404)"
    else
        echo "   ⚠️  Status: $HTTP_STATUS"
    fi
done

echo ""
echo "📊 Summary:"
echo "   API URL: http://localhost:8002"
echo "   API Key: $API_KEY"
echo "   Docs:    http://localhost:8002/docs"
