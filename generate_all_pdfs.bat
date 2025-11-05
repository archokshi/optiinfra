@echo off
echo ========================================
echo OptiInfra Comprehensive Documentation
echo PDF Generation Script
echo ========================================
echo.

REM Check if Pandoc is installed
where pandoc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Pandoc is not installed or not in PATH
    echo Please install Pandoc from: https://pandoc.org/installing.html
    echo Or install via Chocolatey: choco install pandoc
    pause
    exit /b 1
)

echo Pandoc found! Starting HTML generation...
echo.

REM PHASE4 - Application Agent
echo [1/5] Generating PHASE4 - Application Agent HTML...
cd "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\application-agent"
pandoc PHASE4_Application_Agent_Comprehensive_Document_D.1.md PHASE4_Application_Agent_Comprehensive_Document_D.2.md PHASE4_Application_Agent_Comprehensive_Document_D.3.md PHASE4_Application_Agent_Comprehensive_Document_D.4.md PHASE4_Application_Agent_Comprehensive_Document_D.5.md -o PHASE4_Application_Agent_Comprehensive_Document.html --toc --number-sections --standalone --self-contained
if %ERRORLEVEL% EQU 0 (
    echo    SUCCESS: PHASE4 PDF created
) else (
    echo    ERROR: PHASE4 PDF generation failed
)
echo.

REM PHASE3 - Resource Agent
echo [2/5] Generating PHASE3 - Resource Agent HTML...
cd "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\resource-agent"
pandoc PHASE3_Resource_Agent_Comprehensive_Document_D.1.md PHASE3_Resource_Agent_Comprehensive_Document_D.2.md PHASE3_Resource_Agent_Comprehensive_Document_D.3.md PHASE3_Resource_Agent_Comprehensive_Document_D.4.md PHASE3_Resource_Agent_Comprehensive_Document_D.5.md -o PHASE3_Resource_Agent_Comprehensive_Document.html --toc --number-sections --standalone --self-contained
if %ERRORLEVEL% EQU 0 (
    echo    SUCCESS: PHASE3 PDF created
) else (
    echo    ERROR: PHASE3 PDF generation failed
)
echo.

REM PHASE2 - Performance Agent
echo [3/5] Generating PHASE2 - Performance Agent HTML...
cd "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\performance-agent"
pandoc PHASE2_Performance_Agent_Comprehensive_Document_D.1.md PHASE2_Performance_Agent_Comprehensive_Document_D.2.md PHASE2_Performance_Agent_Comprehensive_Document_D.3.md PHASE2_Performance_Agent_Comprehensive_Document_D.4.md PHASE2_Performance_Agent_Comprehensive_Document_D.5.md -o PHASE2_Performance_Agent_Comprehensive_Document.html --toc --number-sections --standalone --self-contained
if %ERRORLEVEL% EQU 0 (
    echo    SUCCESS: PHASE2 PDF created
) else (
    echo    ERROR: PHASE2 PDF generation failed
)
echo.

REM PHASE1 - Cost Agent
echo [4/5] Generating PHASE1 - Cost Agent HTML...
cd "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\cost-agent"
pandoc PHASE1_Cost_Agent_Comprehensive_Document_D.1.md PHASE1_Cost_Agent_Comprehensive_Document_D.2.md PHASE1_Cost_Agent_Comprehensive_Document_D.3.md PHASE1_Cost_Agent_Comprehensive_Document_D.4.md PHASE1_Cost_Agent_Comprehensive_Document_D.5.md -o PHASE1_Cost_Agent_Comprehensive_Document.html --toc --number-sections --standalone --self-contained
if %ERRORLEVEL% EQU 0 (
    echo    SUCCESS: PHASE1 PDF created
) else (
    echo    ERROR: PHASE1 PDF generation failed
)
echo.

REM PHASE0 - Orchestrator
echo [5/5] Generating PHASE0 - Orchestrator HTML...
cd "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\orchestrator"
pandoc PHASE0_Orchestrator_Comprehensive_Document_D.1.md PHASE0_Orchestrator_Comprehensive_Document_D.2.md PHASE0_Orchestrator_Comprehensive_Document_D.3.md PHASE0_Orchestrator_Comprehensive_Document_D.4.md PHASE0_Orchestrator_Comprehensive_Document_D.5.md -o PHASE0_Orchestrator_Comprehensive_Document.html --toc --number-sections --standalone --self-contained
if %ERRORLEVEL% EQU 0 (
    echo    SUCCESS: PHASE0 PDF created
) else (
    echo    ERROR: PHASE0 PDF generation failed
)
echo.

echo ========================================
echo HTML Generation Complete!
echo ========================================
echo.
echo Generated PDFs:
echo   - services/application-agent/PHASE4_Application_Agent_Comprehensive_Document.html
echo   - services/resource-agent/PHASE3_Resource_Agent_Comprehensive_Document.html
echo   - services/performance-agent/PHASE2_Performance_Agent_Comprehensive_Document.html
echo   - services/cost-agent/PHASE1_Cost_Agent_Comprehensive_Document.html
echo   - services/orchestrator/PHASE0_Orchestrator_Comprehensive_Document.html
echo.
echo To convert to PDF: Open each HTML file in a browser and use Print to PDF
echo.
pause
