#!/bin/bash
set -e

echo "🔧 Fixing Docker and Docker Compose Issues..."

# 1. Fix Dockerfile permissions
echo "1. Updating Dockerfile..."
cat > Dockerfile << 'DOCKERFILE_EOF'
# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app /app

# Create non-root user
RUN groupadd -r wazuh && useradd -r -g wazuh -s /bin/bash -m wazuh

# Create necessary directories
RUN mkdir -p /data /logs /git-repo

# Copy entrypoint script first and set permissions
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh && \
    chown wazuh:wazuh entrypoint.sh

# Set ownership after permissions are set
RUN chown -R wazuh:wazuh /app /data /logs /git-repo

# Switch to non-root user
USER wazuh

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV GIT_REPO_PATH=/git-repo
ENV DATABASE_PATH=/data/deployments.db
ENV LOG_PATH=/logs/wazuh-api.log

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
DOCKERFILE_EOF

echo "✅ Dockerfile updated"

# 2. Ensure entrypoint.sh is executable
chmod +x entrypoint.sh

# 3. Install docker compose plugin
echo "2. Installing Docker Compose plugin..."
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Install docker compose plugin
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Alternatively install via curl if apt fails
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose via curl..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 4. Build with new Dockerfile
echo "3. Building Docker image..."
docker build -t wazuh-api-server:latest .

echo ""
echo "✅ All fixes applied!"
echo ""
echo "Now you can run:"
echo "  docker compose up -d        # Start containers"
echo "  make up                    # Or use Makefile"
echo ""
echo "Test with:"
echo "  curl http://localhost:8000/health"
