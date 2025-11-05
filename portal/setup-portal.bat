@echo off
echo Creating OptiInfra Portal Directory Structure...

REM Create directories
mkdir lib 2>nul
mkdir components\ui 2>nul
mkdir components\layout 2>nul
mkdir components\dashboard 2>nul
mkdir app\api\health 2>nul
mkdir "app\(dashboard)" 2>nul
mkdir "app\(dashboard)\cost" 2>nul
mkdir "app\(dashboard)\performance" 2>nul
mkdir "app\(dashboard)\resource" 2>nul
mkdir "app\(dashboard)\application" 2>nul

echo Directories created successfully!
echo.
echo Next: Creating core files...
