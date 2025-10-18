#!/bin/bash
set -e

echo "🛑 Stopping OptiInfra services..."

# Stop all services
docker-compose down

echo "✅ All services stopped successfully!"
echo ""
echo "Run 'make dev' or 'make up' to start services again"
