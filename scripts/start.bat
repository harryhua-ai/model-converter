@echo off
REM NE301 Model Converter 启动脚本
REM 支持 Windows

echo Starting NE301 Model Converter...
echo.

REM 检查 Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python 3 not found. Please install Python 3.11+
    echo Visit: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%

REM 检查 Node.js
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Node.js/npm not found. Please install Node.js 18+
    echo Visit: https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo Found Node %NODE_VERSION%, npm %NPM_VERSION%
echo.

REM 安装后端依赖
echo Installing backend dependencies...
cd /d "%~dp0backend"
if exist requirements.txt (
    pip install -r requirements.txt
    echo Backend dependencies installed
) else (
    echo Warning: requirements.txt not found
)
echo.

REM 构建前端
echo Building frontend...
cd /d "%~dp0frontend"
if exist package.json (
    call npm install
    call npm run build
    echo Frontend built successfully
) else (
    echo Warning: package.json not found
)
echo.

REM 启动服务器
echo Starting server...
echo Open http://localhost:8000 in your browser
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
