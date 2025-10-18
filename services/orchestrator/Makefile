.PHONY: help build run test clean docker-build docker-run

# Variables
APP_NAME=orchestrator
DOCKER_IMAGE=optiinfra-orchestrator
VERSION=0.1.0

help:
	@echo "OptiInfra Orchestrator - Build Commands"
	@echo "========================================"
	@echo "make build        - Build Go binary"
	@echo "make run          - Run locally"
	@echo "make test         - Run tests"
	@echo "make clean        - Clean build artifacts"
	@echo "make docker-build - Build Docker image"
	@echo "make docker-run   - Run in Docker"

build:
	@echo "Building $(APP_NAME)..."
	go build -o bin/$(APP_NAME) ./cmd/orchestrator

run:
	@echo "Running $(APP_NAME)..."
	go run ./cmd/orchestrator

test:
	@echo "Running tests..."
	go test -v -race -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

clean:
	@echo "Cleaning..."
	rm -rf bin/
	rm -f coverage.out coverage.html

docker-build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(VERSION) -t $(DOCKER_IMAGE):latest .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8080:8080 --name $(APP_NAME) $(DOCKER_IMAGE):latest

fmt:
	@echo "Formatting code..."
	go fmt ./...

lint:
	@echo "Linting code..."
	go vet ./...

deps:
	@echo "Downloading dependencies..."
	go mod download
	go mod tidy
