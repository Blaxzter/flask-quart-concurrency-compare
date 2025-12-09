#!/bin/bash
# Convenient Docker commands for the IO benchmark suite

case "$1" in
  build)
    echo "Building all Docker images..."
    docker-compose build
    ;;
  
  up)
    echo "Starting all services..."
    docker-compose up -d
    echo ""
    echo "Waiting for services to be healthy..."
    sleep 10
    docker-compose ps
    ;;
  
  down)
    echo "Stopping all services..."
    docker-compose down
    ;;
  
  logs)
    echo "Showing logs..."
    docker-compose logs -f
    ;;
  
  restart)
    echo "Restarting all services..."
    docker-compose down
    docker-compose up -d
    ;;
  
  clean)
    echo "Cleaning up containers and images..."
    docker-compose down -v --rmi all
    ;;
  
  benchmark)
    echo "Running benchmark..."
    python benchmark_docker.py
    ;;
  
  test)
    echo "Testing individual endpoints..."
    echo ""
    echo "FastAPI health:"
    curl -s http://localhost:8001/health | python -m json.tool
    echo ""
    echo "Flask health:"
    curl -s http://localhost:8002/health | python -m json.tool
    echo ""
    echo "Quart health:"
    curl -s http://localhost:8003/health | python -m json.tool
    ;;
  
  stats)
    echo "Container resource usage:"
    docker stats --no-stream io-benchmark-fastapi io-benchmark-flask io-benchmark-quart
    ;;
  
  *)
    echo "IO Benchmark Docker Commands"
    echo "============================"
    echo ""
    echo "Usage: ./docker-commands.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build      - Build all Docker images"
    echo "  up         - Start all services in background"
    echo "  down       - Stop all services"
    echo "  logs       - Show container logs"
    echo "  restart    - Restart all services"
    echo "  clean      - Remove all containers and images"
    echo "  benchmark  - Run the benchmark suite"
    echo "  test       - Test individual endpoints"
    echo "  stats      - Show container resource usage"
    echo ""
    echo "Examples:"
    echo "  ./docker-commands.sh build"
    echo "  ./docker-commands.sh up"
    echo "  ./docker-commands.sh benchmark"
    echo "  ./docker-commands.sh down"
    ;;
esac

