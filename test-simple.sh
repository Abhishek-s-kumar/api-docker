#!/bin/bash
set -e

echo "🧪 Simple Test Script"
echo "===================="

# Clean up
docker compose down 2>/dev/null || true
docker rm -f wazuh-api-test 2>/dev/null || true

# Create a super simple Dockerfile
cat > Dockerfile.test << 'DOCKER_EOF'
FROM python:3.11-slim

WORKDIR /app

# Copy minimal files
COPY app.py .
COPY requirements.txt .

# Install
RUN pip install --no-cache-dir -r requirements.txt

# Expose
EXPOSE 8000

# Simple command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKER_EOF

# Build
docker build -f Dockerfile.test -t wazuh-test:simple .

# Run
docker run -d --name wazuh-api-test -p 8003:8000 wazuh-test:simple

# Wait
sleep 5

# Test
echo "Testing on port 8003..."
if curl -s http://localhost:8003/health > /dev/null; then
    echo "✅ SUCCESS! API is running"
    curl -s http://localhost:8003/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8003/health
else
    echo "❌ FAILED! Checking logs..."
    docker logs wazuh-api-test
fi

# Cleanup
docker stop wazuh-api-test
docker rm wazuh-api-test
