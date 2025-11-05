@echo off
echo ========================================
echo Starting All OptiInfra Agent Services
echo ========================================
echo.

REM Check if databases are running
echo Checking database services...
docker ps | findstr "optiinfra-postgres" >nul
if errorlevel 1 (
    echo ERROR: PostgreSQL not running. Start with: docker-compose up -d
    exit /b 1
)

echo Database services are running
echo.

REM Start Cost Agent (Port 8001)
echo Starting Cost Agent on port 8001...
start "Cost Agent" cmd /k "cd services\cost-agent && python src\main.py"
timeout /t 3 >nul

REM Start Performance Agent (Port 8002)
echo Starting Performance Agent on port 8002...
start "Performance Agent" cmd /k "cd services\performance-agent && python src\main.py"
timeout /t 3 >nul

REM Start Resource Agent (Port 8003)
echo Starting Resource Agent on port 8003...
start "Resource Agent" cmd /k "cd services\resource-agent && python src\main.py"
timeout /t 3 >nul

REM Start Application Agent (Port 8004)
echo Starting Application Agent on port 8004...
start "Application Agent" cmd /k "cd services\application-agent && python src\main.py"
timeout /t 3 >nul

echo.
echo ========================================
echo All agents started successfully!
echo ========================================
echo.
echo Services running on:
echo   - Cost Agent:         http://localhost:8001
echo   - Performance Agent:  http://localhost:8002
echo   - Resource Agent:     http://localhost:8003
echo   - Application Agent:  http://localhost:8004
echo.
echo Wait 30 seconds for services to be ready, then run:
echo   python -m pytest tests/ -v
echo.
pause
