@echo off
setlocal

set ROOT_DIR=%CD%
set COST_AGENT_DIR=%ROOT_DIR%\services\cost-agent
set PERF_AGENT_DIR=%ROOT_DIR%\services\performance-agent
set RES_AGENT_DIR=%ROOT_DIR%\services\resource-agent
set APP_AGENT_DIR=%ROOT_DIR%\services\application-agent

echo ========================================
echo Starting OptiInfra Agents (Proper Method)
echo ========================================
echo.

echo Starting Cost Agent on port 8001...
start "Cost Agent" cmd /k "cd /d %COST_AGENT_DIR% && set PYTHONPATH=%PYTHONPATH%;%ROOT_DIR%;%COST_AGENT_DIR% && uvicorn src.main:app --host 0.0.0.0 --port 8001"
timeout /t 2 >nul

echo Starting Performance Agent on port 8002...
start "Performance Agent" cmd /k "cd /d %PERF_AGENT_DIR% && set PYTHONPATH=%PYTHONPATH%;%ROOT_DIR%;%PERF_AGENT_DIR% && uvicorn src.main:app --host 0.0.0.0 --port 8002"
timeout /t 2 >nul

echo Starting Resource Agent on port 8003...
start "Resource Agent" cmd /k "cd /d %RES_AGENT_DIR% && set PYTHONPATH=%PYTHONPATH%;%ROOT_DIR%;%RES_AGENT_DIR% && uvicorn src.main:app --host 0.0.0.0 --port 8003"
timeout /t 2 >nul

echo Starting Application Agent on port 8004...
start "Application Agent" cmd /k "cd /d %APP_AGENT_DIR% && set PYTHONPATH=%PYTHONPATH%;%ROOT_DIR%;%APP_AGENT_DIR% && uvicorn src.main:app --host 0.0.0.0 --port 8004"
timeout /t 2 >nul

echo.
echo ========================================
echo All agents starting...
echo ========================================
echo.
echo Services will be available on:
echo   - Cost Agent:         http://localhost:8001
echo   - Performance Agent:  http://localhost:8002
echo   - Resource Agent:     http://localhost:8003
echo   - Application Agent:  http://localhost:8004
echo.
echo Wait 30 seconds for services to fully start
echo Then check: http://localhost:8001/health
echo.
endlocal
pause
