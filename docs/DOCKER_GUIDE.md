# Docker Production Benchmark Guide

This guide explains how to run realistic production benchmarks using Docker containers with proper WSGI/ASGI servers.

## Why Docker + Production Servers?

Running benchmarks with production-ready servers gives you realistic performance metrics:

| Setup       | Server    | Type         | Use Case                                |
| ----------- | --------- | ------------ | --------------------------------------- |
| **Flask**   | Gunicorn  | WSGI (sync)  | Traditional production Flask deployment |
| **Quart**   | Hypercorn | ASGI (async) | Modern async production deployment      |
| **FastAPI** | Uvicorn   | ASGI (async) | Test server for IO simulation           |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │   FastAPI    │   │    Flask     │   │    Quart     │   │
│  │   Uvicorn    │   │   Gunicorn   │   │  Hypercorn   │   │
│  │              │◄──┤              │◄──┤              │   │
│  │  Port 8001   │   │  Port 8002   │   │  Port 8003   │   │
│  │              │   │              │   │              │   │
│  │  (IO Sim)    │   │  (Sync)      │   │  (Async)     │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│        ▲                   ▲                   ▲           │
└────────┼───────────────────┼───────────────────┼───────────┘
         │                   │                   │
         └───────────────────┴───────────────────┘
                      Benchmark Script
```

## Quick Start

### 1. Build and Start All Services

**Using convenience scripts:**

Windows:

```cmd
docker-commands.bat build
docker-commands.bat up
```

Linux/Mac:

```bash
chmod +x docker-commands.sh
./docker-commands.sh build
./docker-commands.sh up
```

**Or directly with docker-compose:**

```bash
docker-compose up --build -d
```

### 2. Verify Services are Running

```bash
# Windows
docker-commands.bat test

# Linux/Mac
./docker-commands.sh test

# Or manually
curl http://localhost:8001/health  # FastAPI
curl http://localhost:8002/health  # Flask/Gunicorn
curl http://localhost:8003/health  # Quart/Hypercorn
```

### 3. Run the Benchmark

```bash
# Windows
docker-commands.bat benchmark

# Linux/Mac
./docker-commands.sh benchmark

# Or directly
python benchmark_docker.py
```

### 4. View Logs (Optional)

```bash
docker-compose logs -f
```

### 5. Stop Services

```bash
# Windows
docker-commands.bat down

# Linux/Mac
./docker-commands.sh down

# Or directly
docker-compose down
```

## Expected Results

### Production Benchmark Output

```
================================================================================
Production IO Benchmark: Quart/Hypercorn (ASGI) vs Flask/Gunicorn (WSGI)
================================================================================

1. Checking Docker containers availability...
   ✅ FastAPI test server (port 8001) is running
   ✅ Flask/Gunicorn server (port 8002) is running
   ✅ Quart/Hypercorn server (port 8003) is running

2. Running benchmark scenarios...

Scenario 2: Low Concurrency (5 requests)
  Results:
    Metric                         Flask/Gunicorn            Quart/Hypercorn            Improvement
    -----------------------------------------------------------------------------------------------
    Total Duration                      5.234s                     1.156s                 4.53x
    Requests/sec                         0.96                       4.33                  4.53x

  ✅ Good! Significant async benefit

Scenario 5: Stress Test (50 requests)
  Results:
    Metric                         Flask/Gunicorn            Quart/Hypercorn            Improvement
    -----------------------------------------------------------------------------------------------
    Total Duration                     15.892s                     0.412s                38.59x
    Requests/sec                         3.15                     121.36                 38.59x

  🚀 Excellent! Async provides major speedup

3. Overall Summary
  Average Speedup: 12.34x
  Maximum Speedup: 38.59x
  Minimum Speedup: 1.12x

  🎉 Excellent results! Quart/Hypercorn provides significant performance benefits

  Production Recommendations:
  ✅ Strong case for migrating to Quart/Hypercorn (ASGI)
  ✅ Expected production improvements: faster response times, higher throughput
```

## Configuration Details

### Gunicorn (Flask/WSGI)

```dockerfile
CMD ["gunicorn",
     "--bind", "0.0.0.0:8002",
     "--workers", "4",           # Multiple worker processes
     "--threads", "2",           # Threads per worker
     "--timeout", "120",
     "flask_comparison_server:app"]
```

**Characteristics:**

- **Workers**: 4 separate processes
- **Threads**: 2 per worker (8 total threads)
- **Concurrency**: Limited by thread count
- **Model**: Pre-fork worker (process-based)

### Hypercorn (Quart/ASGI)

```dockerfile
CMD ["hypercorn",
     "--bind", "0.0.0.0:8003",
     "--workers", "4",                # Multiple worker processes
     "--worker-class", "asyncio",     # Async worker
     "quart_comparison_server:app"]
```

**Characteristics:**

- **Workers**: 4 async workers
- **Concurrency**: Thousands of concurrent connections per worker
- **Model**: Async/await with event loop
- **Advantage**: Non-blocking IO

### Uvicorn (FastAPI/ASGI)

```dockerfile
CMD ["uvicorn",
     "fastapi_server:app",
     "--host", "0.0.0.0",
     "--port", "8001",
     "--workers", "2"]
```

**Characteristics:**

- **Workers**: 2 async workers (test server, doesn't need many)
- **Concurrency**: High
- **Model**: Async/await

## Docker Commands Reference

### Using Helper Scripts

```bash
# Build all images
./docker-commands.sh build

# Start all services
./docker-commands.sh up

# Stop all services
./docker-commands.sh down

# View logs
./docker-commands.sh logs

# Restart services
./docker-commands.sh restart

# Test endpoints
./docker-commands.sh test

# View resource usage
./docker-commands.sh stats

# Run benchmark
./docker-commands.sh benchmark

# Clean everything
./docker-commands.sh clean
```

### Direct Docker Compose

```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f [service-name]

# Stop
docker-compose down

# Restart specific service
docker-compose restart flask-server

# Scale a service (not recommended for this benchmark)
docker-compose up --scale flask-server=2

# View status
docker-compose ps

# Clean up everything
docker-compose down -v --rmi all
```

### Individual Container Management

```bash
# View logs for specific service
docker-compose logs -f flask-server

# Execute command in container
docker-compose exec flask-server /bin/bash

# Restart single service
docker-compose restart quart-server

# Stop single service
docker-compose stop fastapi-server

# Start single service
docker-compose start fastapi-server
```

## Performance Monitoring

### Resource Usage

```bash
# Real-time stats
docker stats io-benchmark-fastapi io-benchmark-flask io-benchmark-quart

# Or using helper
./docker-commands.sh stats
```

You'll see:

- **CPU %**: CPU usage per container
- **MEM USAGE**: Memory consumption
- **NET I/O**: Network traffic
- **BLOCK I/O**: Disk I/O

### Expected Resource Usage

| Service         | CPU (idle) | CPU (load) | Memory |
| --------------- | ---------- | ---------- | ------ |
| FastAPI/Uvicorn | ~0%        | 5-10%      | ~50MB  |
| Flask/Gunicorn  | ~0%        | 40-60%     | ~200MB |
| Quart/Hypercorn | ~0%        | 5-15%      | ~80MB  |

**Key Observation**: Async servers (Quart/Hypercorn) use significantly less CPU during IO-bound operations.

## Manual Testing

### Test Individual Endpoints

```bash
# Quart/Hypercorn - should complete in ~1s
curl "http://localhost:8003/benchmark/quart-io-test?delay=1.0&concurrent=10"

# Flask/Gunicorn - will take ~10s
curl "http://localhost:8002/benchmark/flask-io-test?delay=1.0&concurrent=10"
```

### Stress Testing

```bash
# Heavy load on Quart (handles well)
curl "http://localhost:8003/benchmark/quart-io-test?delay=0.5&concurrent=100"

# Heavy load on Flask (may struggle)
curl "http://localhost:8002/benchmark/flask-io-test?delay=0.5&concurrent=100"
```

## Troubleshooting

### Containers Not Starting

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Port Conflicts

If ports 8001-8003 are in use:

1. Edit `docker-compose.yml`:

```yaml
ports:
  - "9001:8001" # Changed external port
```

2. Update `benchmark_docker.py` URLs accordingly

### Network Issues

```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

### Performance Issues

1. **Increase Docker resources**: Docker Desktop → Settings → Resources
2. **Reduce workers**: Edit Dockerfiles, change `--workers` value
3. **Check host system**: Close other applications

## Production Deployment Insights

### When to Use Gunicorn + Flask (WSGI)

✅ **Good for:**

- CPU-bound operations
- Simple CRUD APIs
- Legacy codebases
- When async isn't needed

❌ **Limitations:**

- Poor concurrent IO performance
- Higher resource usage
- Thread/process bound concurrency

### When to Use Hypercorn + Quart (ASGI)

✅ **Good for:**

- IO-bound operations
- External API calls
- LLM integrations
- WebSocket support
- High concurrency needs
- Modern async Python code

❌ **Considerations:**

- Requires async/await code
- More complex debugging
- Newer ecosystem

## Next Steps

1. **Run the benchmark** with Docker
2. **Compare results** to dev server benchmarks
3. **Identify real production gains** for your use case
4. **Consider migration strategy** if results are compelling
5. **Test with your actual workload** patterns

## Additional Resources

- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Hypercorn Documentation](https://hypercorn.readthedocs.io/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Ready to see production-realistic results? Run `./docker-commands.sh up && python benchmark_docker.py`** 🐳
