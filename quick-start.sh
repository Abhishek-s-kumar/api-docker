#!/bin/bash
set -e

echo "🚀 Wazuh API Server - Quick Start"
echo "================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Please log out and back in for group changes."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed."
fi

echo ""
echo "Building Docker image..."
docker build -t wazuh-api-server:latest .

echo ""
echo "Starting containers..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

echo ""
echo "Waiting for API to start..."
sleep 10

echo ""
echo "✅ Wazuh API Server is running!"
echo ""
echo "📡 API URL: http://localhost:8080"
echo "🏥 Health check: http://localhost:8080/health"
echo "📚 API Documentation: http://localhost:8080/docs"
echo ""
echo "🔑 To get a test API key:"
echo "   docker compose exec wazuh-api sqlite3 /data/deployments.db \\"
echo "     \"SELECT key FROM api_keys WHERE server_id = 'test-server-01' LIMIT 1;\""
echo ""
echo "📋 Useful commands:"
echo "   docker compose logs -f      # View logs"
echo "   docker compose exec wazuh-api /bin/bash  # Enter container"
echo "   docker compose down         # Stop containers"
echo ""
echo "🐳 To update with your Git repository:"
echo "   Edit docker-compose.yml and set GIT_REPO_URL to your rules repository"
echo "   Then run: docker compose down && docker compose up -d"
