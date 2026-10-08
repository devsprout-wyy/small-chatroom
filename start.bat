@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   极简聊天室 - 一键启动
echo ========================================
echo.
if not exist "venv\Scripts\python.exe" (
    echo [1/4] First run: creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to create venv. Is Python installed and on PATH?
        echo         Try: py -3.14 -m venv venv
        pause
        exit /b 1
    )
    echo [2/4] Installing dependencies...
    call "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual environment found.
    echo [2/4] Checking dependencies...
    call "venv\Scripts\python.exe" -c "import fastapi, uvicorn, websockets" >nul 2>&1
    if errorlevel 1 (
        echo       Missing packages, installing...
        call "venv\Scripts\python.exe" -m pip install -r requirements.txt
    ) else (
        echo       All dependencies OK.
    )
)
echo [3/4] Starting server...
echo.
echo   Chat page : http://127.0.0.1:8010/
echo   API docs  : http://127.0.0.1:8010/docs
echo.
echo   Press Ctrl+C to stop the server.
echo ========================================
echo.
start "" http://127.0.0.1:8010/
call "venv\Scripts\python.exe" main.py
echo.
echo Server stopped.
pause