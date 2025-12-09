@echo off
REM Convenient Docker commands for the IO benchmark suite (Windows)

IF "%1"=="build" (
    echo Building all Docker images...
    docker-compose build
    GOTO :EOF
)

IF "%1"=="up" (
    echo Starting all services...
    docker-compose up -d
    echo.
    echo Waiting for services to be healthy...
    timeout /t 10 /nobreak >nul
    docker-compose ps
    GOTO :EOF
)

IF "%1"=="down" (
    echo Stopping all services...
    docker-compose down
    GOTO :EOF
)

IF "%1"=="logs" (
    echo Showing logs...
    docker-compose logs -f
    GOTO :EOF
)

IF "%1"=="restart" (
    echo Restarting all services...
    docker-compose down
    docker-compose up -d
    GOTO :EOF
)

IF "%1"=="clean" (
    echo Cleaning up containers and images...
    docker-compose down -v --rmi all
    GOTO :EOF
)

IF "%1"=="benchmark" (
    echo Running benchmark...
    python benchmark_docker.py
    GOTO :EOF
)

IF "%1"=="test" (
    echo Testing individual endpoints...
    echo.
    echo FastAPI health:
    curl -s http://localhost:8001/health
    echo.
    echo Flask health:
    curl -s http://localhost:8002/health
    echo.
    echo Quart health:
    curl -s http://localhost:8003/health
    GOTO :EOF
)

IF "%1"=="stats" (
    echo Container resource usage:
    docker stats --no-stream io-benchmark-fastapi io-benchmark-flask io-benchmark-quart
    GOTO :EOF
)

echo IO Benchmark Docker Commands
echo ============================
echo.
echo Usage: docker-commands.bat [command]
echo.
echo Commands:
echo   build      - Build all Docker images
echo   up         - Start all services in background
echo   down       - Stop all services
echo   logs       - Show container logs
echo   restart    - Restart all services
echo   clean      - Remove all containers and images
echo   benchmark  - Run the benchmark suite
echo   test       - Test individual endpoints
echo   stats      - Show container resource usage
echo.
echo Examples:
echo   docker-commands.bat build
echo   docker-commands.bat up
echo   docker-commands.bat benchmark
echo   docker-commands.bat down

