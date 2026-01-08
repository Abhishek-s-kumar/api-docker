#!/bin/bash
set -e

echo "🚀 Wazuh API Server - Starting on port 8001"
echo "==========================================="

# Clean up any existing containers
echo "🧹 Cleaning up previous containers..."
docker compose down 2>/dev/null || true
docker rm -f wazuh-api 2>/dev/null || true

# Build the image
echo "🔨 Building Docker image..."
docker build -t wazuh-api-server:latest .

# Start the container
echo "🚀 Starting container..."
docker compose up -d

# Wait for it to start
echo "⏳ Waiting for API to initialize..."
for i in {1..30}; do
    if docker compose logs wazuh-api 2>/dev/null | grep -q "Starting Wazuh API Server"; then
        echo "✅ API is starting..."
        break
    fi
    sleep 2
done

# Show logs and test
echo ""
echo "📋 Container status:"
docker compose ps

echo ""
echo "📜 Recent logs:"
docker compose logs --tail=20 wazuh-api

echo ""
echo "🧪 Testing API health..."
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ API is responding!"
    curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8001/health
else
    echo "❌ API not responding yet. Check logs with: docker compose logs -f wazuh-api"
fi

echo ""
echo "🔑 To get a test API key:"
echo "   docker compose exec wazuh-api sqlite3 /data/deployments.db \\"
echo "     \"SELECT key FROM api_keys WHERE server_id = 'test-server-01' LIMIT 1;\""

echo ""
echo "📡 API URL: http://localhost:8001"
echo "🏥 Health:  http://localhost:8001/health"
echo "📚 Docs:    http://localhost:8001/docs"
echo ""
echo "📋 Commands:"
echo "   docker compose logs -f wazuh-api    # View logs"
echo "   docker compose exec wazuh-api bash  # Enter container"
echo "   docker compose down                 # Stop container"
