#!/bin/bash
set -e

echo "🚀 OptiInfra Setup Starting..."

# Check required tools
echo "📋 Checking required tools..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git first."
    exit 1
fi

echo "✅ All required tools found"

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please update with your values."
else
    echo "✅ .env file already exists"
fi

# Pull Docker images
echo "📥 Pulling Docker images..."
docker-compose pull

# Create network
echo "🌐 Creating Docker network..."
docker network create optiinfra-network 2>/dev/null || echo "Network already exists"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your credentials"
echo "2. Run: make dev (or make up for detached mode)"
echo "3. Run: make verify (to check all services)"
echo ""
