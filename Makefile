.PHONY: help build up down logs shell restart clean test backup

# Colors
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

# Use docker compose (with space) which is the newer version
DOCKER_COMPOSE=docker compose

help:
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo "  build     - Build Docker image"
	@echo "  build-dev - Build development image"
	@echo "  up        - Start containers (production)"
	@echo "  up-dev    - Start containers (development)"
	@echo "  down      - Stop containers"
	@echo "  logs      - View container logs"
	@echo "  shell     - Open shell in container"
	@echo "  restart   - Restart containers"
	@echo "  clean     - Remove containers and volumes"
	@echo "  test      - Test API connection"
	@echo "  backup    - Backup database"
	@echo "  push      - Push to Docker Hub"
	@echo "  deploy    - Deploy to production"

build:
	@echo "$(YELLOW)Building production image...$(NC)"
	docker build -t wazuh-api-server:latest .

build-dev:
	@echo "$(YELLOW)Building development image...$(NC)"
	docker build -t wazuh-api-dev:latest .

up:
	@echo "$(YELLOW)Starting production containers...$(NC)"
	$(DOCKER_COMPOSE) up -d

up-dev:
	@echo "$(YELLOW)Starting development containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.dev.yml up -d

down:
	@echo "$(YELLOW)Stopping containers...$(NC)"
	$(DOCKER_COMPOSE) down

logs:
	@echo "$(YELLOW)Tailing logs...$(NC)"
	$(DOCKER_COMPOSE) logs -f

shell:
	@echo "$(YELLOW)Opening shell in container...$(NC)"
	$(DOCKER_COMPOSE) exec wazuh-api /bin/bash

restart:
	@echo "$(YELLOW)Restarting containers...$(NC)"
	$(DOCKER_COMPOSE) restart

clean:
	@echo "$(YELLOW)Cleaning up...$(NC)"
	$(DOCKER_COMPOSE) down -v
	docker system prune -f

test:
	@echo "$(YELLOW)Testing API connection...$(NC)"
	@curl -s http://localhost:8080/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('✅ $(GREEN)Health check:', data.get('status', 'unknown'), '$(NC)')
    print('   Database:', data.get('database', 'unknown'))
except Exception as e:
    print('❌ $(RED)API test failed:', e, '$(NC)')
"
	@echo ""
	@echo "$(YELLOW)Getting test API key from container...$(NC)"
	@$(DOCKER_COMPOSE) exec wazuh-api sqlite3 /data/deployments.db \
		"SELECT key FROM api_keys WHERE server_id = 'test-server-01' LIMIT 1;" 2>/dev/null | \
		head -1 | xargs -I {} echo "🔑 Test API Key: {}"

backup:
	@echo "$(YELLOW)Backing up database...$(NC)"
	mkdir -p backups
	@$(DOCKER_COMPOSE) exec wazuh-api sqlite3 /data/deployments.db \
		".backup /data/deployments_backup_$(shell date +%Y%m%d_%H%M%S).db"
	@$(DOCKER_COMPOSE) cp wazuh-api:/data/deployments_backup_*.db ./backups/
	@echo "$(GREEN)✅ Backup saved to backups/$(NC)"

push:
	@echo "$(YELLOW)Pushing to Docker Hub...$(NC)"
	@read -p "Docker Hub username: " username; \
	read -p "Docker Hub repository: " repo; \
	docker tag wazuh-api-server:latest $$username/$$repo:latest; \
	docker push $$username/$$repo:latest; \
	echo "$(GREEN)✅ Pushed to Docker Hub: $$username/$$repo:latest$(NC)"

deploy:
	@echo "$(YELLOW)Deploying to production...$(NC)"
	@echo "1. Ensure Docker is installed on production server"
	@echo "2. Copy docker-compose.yml to production server"
	@echo "3. Run: docker compose pull && docker compose up -d"
	@echo ""
	@echo "Quick command:"
	@echo "  scp docker-compose.yml user@production-server:/opt/wazuh-api/"
	@echo "  ssh user@production-server 'cd /opt/wazuh-api && docker compose pull && docker compose up -d'"

status:
	@echo "$(YELLOW)Container status:$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "$(YELLOW)Volume usage:$(NC)"
	@docker system df
