#!/bin/bash

echo "🔍 Verifying OptiInfra Services..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check PostgreSQL
echo -n "PostgreSQL... "
if docker exec optiinfra-postgres pg_isready -U optiinfra &>/dev/null; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
fi

# Check ClickHouse
echo -n "ClickHouse... "
if curl -s http://localhost:8123/ping &>/dev/null; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
fi

# Check Qdrant
echo -n "Qdrant...     "
if curl -s http://localhost:6333/health &>/dev/null; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
fi

# Check Redis
echo -n "Redis...      "
if docker exec optiinfra-redis redis-cli ping | grep -q PONG; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
fi

echo ""
echo "🎉 Infrastructure verification complete!"
