.PHONY: help setup dev up down restart logs verify test lint clean

# Default target
help:
	@echo "OptiInfra Development Commands"
	@echo "==============================="
	@echo "make setup    - Initial setup (run once)"
	@echo "make dev      - Start all services in development mode"
	@echo "make up       - Start all services (detached)"
	@echo "make down     - Stop all services"
	@echo "make restart  - Restart all services"
	@echo "make logs     - View logs (all services)"
	@echo "make verify   - Verify all services are healthy"
	@echo "make test     - Run all tests"
	@echo "make lint     - Run linters on all code"
	@echo "make clean    - Clean up containers and volumes"

# Initial setup
setup:
	@echo "Setting up OptiInfra development environment..."
	@chmod +x scripts/*.sh
	@./scripts/setup.sh

# Start services in development mode (foreground)
dev:
	@echo "Starting OptiInfra services..."
	docker-compose up

# Start services (detached)
up:
	@echo "Starting OptiInfra services (detached)..."
	docker-compose up -d
	@sleep 5
	@make verify

# Stop services
down:
	@echo "Stopping OptiInfra services..."
	docker-compose down

# Restart services
restart:
	@make down
	@make up

# View logs
logs:
	docker-compose logs -f

# Verify all services are healthy
verify:
	@./scripts/verify.sh

# Run all tests
test:
	@./scripts/test.sh

# Run linters
lint:
	@echo "Running linters..."
	@cd services/orchestrator && go fmt ./... && go vet ./...
	@cd services/cost-agent && black src/ tests/ && flake8 src/ tests/
	@cd services/performance-agent && black src/ tests/ && flake8 src/ tests/
	@cd services/resource-agent && black src/ tests/ && flake8 src/ tests/
	@cd services/application-agent && black src/ tests/ && flake8 src/ tests/

# Clean up
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete"
