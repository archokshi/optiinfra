#!/bin/bash
set -e

echo "🚀 Starting OptiInfra services..."

# Start all services
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Verify services
./scripts/verify.sh

echo ""
echo "✅ All services started successfully!"
echo ""
echo "Available services:"
echo "  - PostgreSQL:  localhost:5432"
echo "  - ClickHouse:  localhost:8123"
echo "  - Qdrant:      localhost:6333"
echo "  - Redis:       localhost:6379"
echo ""
echo "Run 'make logs' to view service logs"
echo "Run 'make down' to stop all services"
