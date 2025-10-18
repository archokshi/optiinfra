#!/bin/bash
set -e

echo "🧪 Running OptiInfra Tests..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test Orchestrator (when implemented)
if [ -d "services/orchestrator" ]; then
    echo "Testing Orchestrator..."
    cd services/orchestrator
    if go test ./... -v; then
        echo -e "${GREEN}✅ Orchestrator tests passed${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Orchestrator tests failed${NC}"
        ((TESTS_FAILED++))
    fi
    cd ../..
fi

# Test Cost Agent (when implemented)
if [ -d "services/cost-agent/tests" ]; then
    echo "Testing Cost Agent..."
    cd services/cost-agent
    if pytest tests/ -v; then
        echo -e "${GREEN}✅ Cost Agent tests passed${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Cost Agent tests failed${NC}"
        ((TESTS_FAILED++))
    fi
    cd ../..
fi

# Test Performance Agent (when implemented)
if [ -d "services/performance-agent/tests" ]; then
    echo "Testing Performance Agent..."
    cd services/performance-agent
    if pytest tests/ -v; then
        echo -e "${GREEN}✅ Performance Agent tests passed${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Performance Agent tests failed${NC}"
        ((TESTS_FAILED++))
    fi
    cd ../..
fi

# Test Resource Agent (when implemented)
if [ -d "services/resource-agent/tests" ]; then
    echo "Testing Resource Agent..."
    cd services/resource-agent
    if pytest tests/ -v; then
        echo -e "${GREEN}✅ Resource Agent tests passed${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Resource Agent tests failed${NC}"
        ((TESTS_FAILED++))
    fi
    cd ../..
fi

# Test Application Agent (when implemented)
if [ -d "services/application-agent/tests" ]; then
    echo "Testing Application Agent..."
    cd services/application-agent
    if pytest tests/ -v; then
        echo -e "${GREEN}✅ Application Agent tests passed${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ Application Agent tests failed${NC}"
        ((TESTS_FAILED++))
    fi
    cd ../..
fi

# Summary
echo ""
echo "========================================="
echo "Test Summary:"
echo "  Passed: $TESTS_PASSED"
echo "  Failed: $TESTS_FAILED"
echo "========================================="

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
