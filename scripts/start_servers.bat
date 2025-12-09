@echo off
REM Convenience script to start all servers for benchmarking (Windows)

echo Starting IO Benchmark Test Environment
echo =======================================
echo.

REM Check if we're in the right directory
if not exist "fastapi_server.py" (
    echo Error: Please run this script from the 00_scripts\io_benchmark directory
    exit /b 1
)

echo 1. Starting FastAPI test server on port 8001...
start "FastAPI Test Server" cmd /k python fastapi_server.py

timeout /t 2 /nobreak >nul

echo 2. Starting Flask comparison server on port 8002...
start "Flask Comparison Server" cmd /k python flask_comparison_server.py

timeout /t 2 /nobreak >nul

echo.
echo Servers started!
echo ================
echo FastAPI Test Server:    http://localhost:8001
echo Flask Comparison:       http://localhost:8002
echo.
echo Now start your Quart application (main Respeak backend) and run:
echo   python benchmark.py
echo.
echo To stop the servers, close their respective command windows.

