#!/bin/bash
set -e

echo "🔥 Wazuh API Server - Production Deployment"
echo "==========================================="

# Configuration
IMAGE_NAME="wazuh-api-server"
TAG="latest"
DOMAIN="api.wazuh.yourdomain.com"
EMAIL="admin@yourdomain.com"
SECRET_KEY=$(openssl rand -hex 32)

echo "Generating production configuration..."
cat > docker-compose.prod.yml << COMPOSE_EOF
version: '3.8'

services:
  wazuh-api:
    image: ${IMAGE_NAME}:${TAG}
    container_name: wazuh-api-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      # Production Git repository (YOUR ACTUAL RULES REPO)
      - GIT_REPO_URL=https://github.com/Abhishek-s-kumar/prox-wazuh-ci.git
      - GIT_BRANCH=main
      
      # Security - Generated secure key
      - SECRET_KEY=${SECRET_KEY}
      
      # Server configuration
      - ENVIRONMENT=production
      - WORKERS=4
      - LOG_LEVEL=WARNING
      
      # Database
      - DATABASE_PATH=/data/deployments.db
    volumes:
      - wazuh_data_prod:/data
      - wazuh_logs_prod:/logs
      - wazuh_git_repo_prod:/git-repo
    networks:
      - wazuh-network-prod
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: wazuh-api-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-prod:/etc/nginx/conf.d:ro
      - ./ssl:/etc/nginx/ssl:ro
      - certbot-www:/var/www/certbot
      - certbot-conf:/etc/letsencrypt
    depends_on:
      - wazuh-api
    networks:
      - wazuh-network-prod
    command: "/bin/sh -c 'while :; do sleep 6h & wait \$\${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

volumes:
  wazuh_data_prod:
  wazuh_logs_prod:
  wazuh_git_repo_prod:
  certbot-conf:
  certbot-www:

networks:
  wazuh-network-prod:
COMPOSE_EOF

# Create nginx production config
mkdir -p nginx-prod

cat > nginx-prod/wazuh-api.conf << NGINX_EOF
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};
    
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # API proxy
    location / {
        proxy_pass http://wazuh-api:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINX_EOF

echo ""
echo "✅ Production configuration created!"
echo ""
echo "📋 Next steps:"
echo "1. Build the image: docker build -t ${IMAGE_NAME}:${TAG} ."
echo "2. Update ${DOMAIN} with your actual domain in docker-compose.prod.yml"
echo "3. Start the stack: docker-compose -f docker-compose.prod.yml up -d"
echo "4. Get SSL certificates:"
echo "   docker-compose -f docker-compose.prod.yml run --rm certbot certonly \\"
echo "     --webroot -w /var/www/certbot \\"
echo "     -d ${DOMAIN} \\"
echo "     --email ${EMAIL} \\"
echo "     --agree-tos \\"
echo "     --non-interactive"
echo ""
echo "🔑 Generated SECRET_KEY: ${SECRET_KEY}"
echo "   Save this key securely!"
