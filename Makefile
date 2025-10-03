# BLACK BOX - Makefile
# Convenient commands for development and deployment

.PHONY: help build start stop restart logs clean test

help:
	@echo "BLACK BOX - Available Commands"
	@echo "=============================="
	@echo "make build      - Build all Docker images"
	@echo "make start      - Start all services"
	@echo "make stop       - Stop all services"
	@echo "make restart    - Restart all services"
	@echo "make logs       - View logs (all services)"
	@echo "make status     - Check service status"
	@echo "make health     - Check system health"
	@echo "make clean      - Clean up containers and volumes"
	@echo "make test       - Run test suite"
	@echo "make backup     - Backup database"
	@echo "make setup      - Run system setup (requires sudo)"

build:
	@echo "Building Docker images..."
	docker-compose build

start:
	@echo "Starting BLACK BOX services..."
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@make status

stop:
	@echo "Stopping BLACK BOX services..."
	docker-compose down

restart:
	@echo "Restarting BLACK BOX services..."
	docker-compose restart

logs:
	docker-compose logs -f

status:
	@echo "Service Status:"
	@docker-compose ps
	@echo ""
	@echo "Health Check:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Orchestrator not responding"

health:
	@curl -s http://localhost:8000/health | python3 -m json.tool

metrics:
	@curl -s http://localhost:8000/metrics | python3 -m json.tool

thermal:
	@curl -s http://localhost:8000/thermal/status | python3 -m json.tool

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	docker system prune -f

test:
	@echo "Running test suite..."
	@curl -s -X POST http://localhost:8000/text/interact \
		-H "Content-Type: application/json" \
		-d '{"text": "What time is it?"}' | python3 -m json.tool

backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	@cp data/blackbox.db backups/blackbox_$(shell date +%Y%m%d_%H%M%S).db
	@echo "Backup complete"

setup:
	@echo "Running system setup (requires sudo)..."
	@sudo ./system/setup-jetson.sh

install-service:
	@echo "Installing systemd service..."
	@sudo cp system/blackbox.service /etc/systemd/system/
	@sudo systemctl daemon-reload
	@sudo systemctl enable blackbox
	@echo "Service installed. Start with: sudo systemctl start blackbox"

