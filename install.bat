@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Lollipop MCP - Windows Installer
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ from python.org
    echo         Make sure "Add to PATH" is checked during installation.
    pause
    exit /b 1
)

:: Check Claude Code
call claude --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Claude Code not found. Please install:
    echo         npm install -g @anthropic-ai/claude-code
    pause
    exit /b 1
)

echo [OK] Python found
echo [OK] Claude Code found
echo.

:: Get install directory (where this script is)
set "INSTALL_DIR=%~dp0"
set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"
echo Install directory: %INSTALL_DIR%

:: Create venv
echo.
echo [1/3] Creating Python virtual environment...
if not exist "%INSTALL_DIR%\.venv" (
    python -m venv "%INSTALL_DIR%\.venv"
)
set "VENV_PIP=%INSTALL_DIR%\.venv\Scripts\pip.exe"
set "VENV_PYTHON=%INSTALL_DIR%\.venv\Scripts\python.exe"

:: Install dependencies
echo [2/3] Installing dependencies...
"%VENV_PIP%" install -q mcp[cli]>=1.26 httpx>=0.27
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: Ask for connection settings
echo.
echo [3/3] Connection settings
echo.
echo Choose connection mode:
echo   1. Direct IP (single machine - simple)
echo   2. Tailscale (multi-machine - advanced)
echo.
set /p MODE="Enter 1 or 2: "

set "ENV_DIRECT="
set "ENV_TAILSCALE="
set "ENV_SERVER="
set "ENV_CARD="

if "%MODE%"=="1" (
    set /p ENV_DIRECT="Windows machine IP (e.g. 192.168.0.114): "
) else (
    set /p ENV_TAILSCALE="Tailscale API Key (tskey-api-...): "
    set /p ENV_SERVER="Server URL (e.g. https://lolly.example.com, or press Enter to skip): "
    set /p ENV_CARD="Card ID (e.g. XXXX-XXXX-XXXX-XXXX, or press Enter to skip): "
)

:: Generate .mcp.json
echo.
echo Generating .mcp.json...

set "MCP_JSON=%USERPROFILE%\.mcp.json"
set "HUB_PATH=%INSTALL_DIR:\=\\%\\mcp_hub.py"
set "PY_PATH=%INSTALL_DIR:\=\\%\\.venv\\Scripts\\python.exe"

(
echo {
echo   "mcpServers": {
echo     "lollipop": {
echo       "type": "stdio",
echo       "command": "%PY_PATH%",
echo       "args": ["%HUB_PATH%"],
echo       "env": {
if defined ENV_DIRECT (
echo         "LOLLIPOP_DIRECT": "%ENV_DIRECT%"
) else (
echo         "LOLLIPOP_TAILSCALE_KEY": "%ENV_TAILSCALE%",
if defined ENV_SERVER echo         "LOLLIPOP_SERVER_URL": "%ENV_SERVER%",
if defined ENV_CARD echo         "LOLLIPOP_CARD_ID": "%ENV_CARD%"
)
echo       }
echo     }
echo   }
echo }
) > "%MCP_JSON%"

echo [OK] Written to %MCP_JSON%

:: Verify
echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Install path: %INSTALL_DIR%
echo Config: %MCP_JSON%
echo.
echo Next steps:
echo   1. Open a new terminal
echo   2. Run: claude
echo   3. Say: "bot_list" to verify connection
echo   4. Say: "教學" for interactive tutorial
echo.
pause
