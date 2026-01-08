cat > README.md << 'EOF'
# Wazuh API Server - Docker Deployment

A containerized Wazuh API server for managing Wazuh rules and configurations via GitOps.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Abhishek-s-kumar/wazuh-api-docker.git
cd wazuh-api-docker

# Start the API
docker compose up -d

# Get API key
docker compose exec wazuh-api sqlite3 /data/deployments.db \
  "SELECT key FROM api_keys WHERE server_id = 'test-server-01' LIMIT 1;"
