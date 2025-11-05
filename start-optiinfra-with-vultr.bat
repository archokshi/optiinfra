@echo off
setlocal

echo ========================================
echo OptiInfra Full Stack Startup
echo With Vultr + Groq Integration
echo ========================================
echo.

set ROOT_DIR=%CD%

echo [1/6] Starting Docker Services...
echo.
docker-compose up -d

echo.
echo [2/6] Waiting for databases to be ready (30 seconds)...
timeout /t 30 /nobreak

echo.
echo [3/6] Checking service status...
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo [4/6] Starting Cost Agent with Vultr + Groq credentials...
echo.
cd services\cost-agent
start "Cost Agent (Vultr+Groq)" cmd /k "set VULTR_API_KEY=***REMOVED*** && set GROQ_API_KEY=***REMOVED*** && set GROQ_MODEL=gpt-oss-20b && set LLM_ENABLED=true && set DATABASE_URL=postgresql://optiinfra:optiinfra_dev_password@localhost:5432/optiinfra && set CLICKHOUSE_URL=http://localhost:8123 && set REDIS_URL=redis://localhost:6379 && set ORCHESTRATOR_URL=http://localhost:8080 && uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload"

cd %ROOT_DIR%
timeout /t 5 /nobreak

echo.
echo [5/6] Starting other agents...
cd services\performance-agent
start "Performance Agent" cmd /k "set DATABASE_URL=postgresql://optiinfra:optiinfra_dev_password@localhost:5432/optiinfra && set REDIS_URL=redis://localhost:6379 && set GROQ_API_KEY=***REMOVED*** && set GROQ_MODEL=gpt-oss-20b && uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload"

cd %ROOT_DIR%
cd services\resource-agent
start "Resource Agent" cmd /k "set DATABASE_URL=postgresql://optiinfra:optiinfra_dev_password@localhost:5432/optiinfra && set REDIS_URL=redis://localhost:6379 && uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload"

cd %ROOT_DIR%
cd services\application-agent
start "Application Agent" cmd /k "set DATABASE_URL=postgresql://optiinfra:optiinfra_dev_password@localhost:5432/optiinfra && set REDIS_URL=redis://localhost:6379 && set GROQ_API_KEY=***REMOVED*** && set GROQ_MODEL=gpt-oss-20b && uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload"

cd %ROOT_DIR%
timeout /t 10 /nobreak

echo.
echo [6/6] Running validation tests...
echo.

echo Testing service health...
curl -s http://localhost:8001/health > nul 2>&1
if %errorlevel% == 0 (
    echo   [OK] Cost Agent (8001)
) else (
    echo   [WAIT] Cost Agent (8001) - still starting...
)

curl -s http://localhost:8002/health > nul 2>&1
if %errorlevel% == 0 (
    echo   [OK] Performance Agent (8002)
) else (
    echo   [WAIT] Performance Agent (8002) - still starting...
)

curl -s http://localhost:8003/health > nul 2>&1
if %errorlevel% == 0 (
    echo   [OK] Resource Agent (8003)
) else (
    echo   [WAIT] Resource Agent (8003) - still starting...
)

curl -s http://localhost:8004/health > nul 2>&1
if %errorlevel% == 0 (
    echo   [OK] Application Agent (8004)
) else (
    echo   [WAIT] Application Agent (8004) - still starting...
)

curl -s http://localhost:8080/health > nul 2>&1
if %errorlevel% == 0 (
    echo   [OK] Orchestrator (8080)
) else (
    echo   [WAIT] Orchestrator (8080) - still starting...
)

curl -s http://localhost:3001 > nul 2>&1
if %errorlevel% == 0 (
    echo   [OK] Portal (3001)
) else (
    echo   [WAIT] Portal (3001) - still starting...
)

echo.
echo ========================================
echo OptiInfra Stack Started!
echo ========================================
echo.
echo Services available at:
echo   - Cost Agent (Vultr):  http://localhost:8001
echo   - Performance Agent:   http://localhost:8002
echo   - Resource Agent:      http://localhost:8003
echo   - Application Agent:   http://localhost:8004
echo   - Orchestrator:        http://localhost:8080
echo   - Portal Dashboard:    http://localhost:3001
echo   - Prometheus:          http://localhost:9090
echo   - Grafana:             http://localhost:3000
echo.
echo API Keys Configured:
echo   - Vultr API Key:  F73WKY624...CLA
echo   - Groq API Key:   gsk_d3bPGYt...2Mj
echo   - LLM Model:      gpt-oss-20b
echo.
echo Next Steps:
echo   1. Wait 30 seconds for all services to fully start
echo   2. Open Portal: http://localhost:3001
echo   3. Test Vultr: curl http://localhost:8001/api/v1/vultr/account
echo   4. View logs in the opened terminal windows
echo.
echo Press any key to open validation tests...
pause

echo.
echo Running Vultr Integration Tests...
echo.

echo Test 1: Vultr Account Info
curl http://localhost:8001/api/v1/vultr/account
echo.
echo.

echo Test 2: Vultr Billing Data
curl -X POST http://localhost:8001/api/v1/vultr/collect-billing
echo.
echo.

echo Test 3: LLM Recommendations
curl -X POST http://localhost:8001/api/v1/recommendations/generate -H "Content-Type: application/json" -d "{\"customer_id\":\"test_vultr\",\"provider\":\"vultr\"}"
echo.
echo.

echo ========================================
echo Validation Complete!
echo ========================================
echo.
echo Check the terminal windows for detailed logs.
echo.
pause
endlocal
