# IO Benchmark Suite - Complete Summary

A comprehensive testing suite to quantify performance improvements between Quart (async) and Flask (sync) for IO-bound operations using production-ready servers.

## 📦 What's Included

### Core Components

1. **FastAPI Test Server** (`fastapi_server.py`) - Simulates IO operations
2. **Flask/Gunicorn** (`flask_comparison_server.py`) - Sync WSGI benchmark
3. **Quart/Hypercorn** (`quart_comparison_server.py`) - Async ASGI benchmark
4. **Automated Benchmarks** (`benchmark.py`, `benchmark_docker.py`)

### Docker Production Setup

- `Dockerfile.fastapi` - FastAPI with Uvicorn
- `Dockerfile.flask` - Flask with Gunicorn (4 workers, 2 threads)
- `Dockerfile.quart` - Quart with Hypercorn (4 async workers)
- `docker-compose.yml` - Orchestrates all services
- Helper scripts for Windows and Linux/Mac

### Documentation

- `README.md` - Project overview
- `DOCKER_GUIDE.md` - Complete Docker guide
- `DOCKER_QUICKSTART.md` - 3-command quick start
- `pyproject.toml` - Modern Python package config

## 🚀 Quick Start Options

### Option 1: Docker (Production-Ready) ⭐ **RECOMMENDED**

```bash
cd 00_scripts/io_benchmark
docker-compose up --build -d
python benchmark_docker.py
docker-compose down
```

**Why Docker?**

- ✅ Production servers (Gunicorn, Hypercorn)
- ✅ Realistic performance metrics
- ✅ Isolated environments
- ✅ Easy to reproduce

### Option 2: Development Setup

```bash
cd 00_scripts/io_benchmark
pip install -e .

# Terminal 1
fastapi-server

# Terminal 2
flask-server

# Terminal 3
# Start your Quart app

# Terminal 4
benchmark
```

### Option 3: Classic Python

```bash
cd 00_scripts/io_benchmark
pip install -r requirements.txt

python fastapi_server.py      # Terminal 1
python flask_comparison_server.py  # Terminal 2
python benchmark.py            # Terminal 3
```

## 📊 Expected Results

### Development Servers

```
Average Speedup: 6-8x
Maximum Speedup: 15-20x
```

### Production Servers (Docker)

```
Average Speedup: 10-15x
Maximum Speedup: 30-50x
```

**Key Insight**: Async (Quart/Hypercorn) performs significantly better for IO-bound operations, especially under higher concurrency.

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Benchmark Script                │
│     (Measures Performance)              │
└─────────┬──────────────┬────────────────┘
          │              │
          ▼              ▼
┌─────────────┐   ┌─────────────┐
│   Flask     │   │   Quart     │
│  Gunicorn   │   │  Hypercorn  │
│   (Sync)    │   │   (Async)   │
│  Port 8002  │   │  Port 8003  │
└──────┬──────┘   └──────┬──────┘
       │                 │
       │  Both call      │
       ▼                 ▼
┌──────────────────────────────┐
│      FastAPI/Uvicorn         │
│   (IO Simulation Server)     │
│        Port 8001             │
└──────────────────────────────┘
```

## 📁 File Structure

```
00_scripts/io_benchmark/
├── Docker Files
│   ├── Dockerfile.fastapi
│   ├── Dockerfile.flask
│   ├── Dockerfile.quart
│   ├── docker-compose.yml
│   ├── .dockerignore
│   ├── docker-commands.sh
│   └── docker-commands.bat
│
├── Server Applications
│   ├── fastapi_server.py
│   ├── flask_comparison_server.py
│   └── quart_comparison_server.py
│
├── Benchmark Scripts
│   ├── benchmark.py              # Dev servers
│   ├── benchmark_docker.py       # Docker production
│   └── quick_test.py             # Server health check
│
├── Requirements
│   ├── requirements-fastapi.txt
│   ├── requirements-flask.txt
│   ├── requirements-quart.txt
│   └── pyproject.toml
│
├── Helper Scripts
│   ├── start_servers.sh
│   ├── start_servers.bat
│   ├── Makefile
│   └── __init__.py
│
└── Documentation
    ├── README.md
    ├── DOCKER_GUIDE.md
    ├── DOCKER_QUICKSTART.md
    └── SUMMARY.md (this file)
```

## 🎯 Use Cases

Perfect for testing performance of:

| Use Case             | Expected Speedup | When It Matters                        |
| -------------------- | ---------------- | -------------------------------------- |
| **LLM API calls**    | 5-10x            | Multiple users, parallel requests      |
| **External APIs**    | 3-8x             | Aggregating data from multiple sources |
| **Database queries** | 5-15x            | With async drivers (asyncpg, motor)    |
| **File uploads**     | 4-10x            | Concurrent uploads to cloud storage    |
| **Microservices**    | 5-20x            | Calling multiple internal services     |

## 🔧 Configuration

### Flask/Gunicorn (WSGI)

```dockerfile
--workers 4      # Process-based workers
--threads 2      # Threads per worker
--timeout 120    # Request timeout
```

**Total Concurrency**: ~8 (4 workers × 2 threads)

### Quart/Hypercorn (ASGI)

```dockerfile
--workers 4              # Process-based workers
--worker-class asyncio   # Async event loop
```

**Total Concurrency**: Thousands (event loop per worker)

## 📈 Performance Metrics

### What Gets Measured

1. **Total Duration**: Time to complete all requests
2. **Requests/sec**: Throughput measurement
3. **Speedup Factor**: Flask time ÷ Quart time
4. **Success Rate**: Percentage of successful requests

### Scenarios Tested

| Scenario | Requests | Delay | Expected Speedup |
| -------- | -------- | ----- | ---------------- |
| Baseline | 1        | 0.5s  | ~1x (similar)    |
| Low      | 5        | 1.0s  | ~5x              |
| Medium   | 10       | 1.0s  | ~10x             |
| High     | 20       | 0.5s  | ~20x             |
| Stress   | 50       | 0.3s  | ~50x             |

## 🎓 Key Learnings

### When Async Wins

✅ **High concurrency**: Multiple simultaneous requests  
✅ **IO-bound**: Waiting for network, disk, external APIs  
✅ **Long operations**: Database queries, file processing  
✅ **Real-time**: WebSockets, SSE, streaming

### When Sync is Fine

✅ **Low concurrency**: Few simultaneous users  
✅ **CPU-bound**: Heavy computation, data processing  
✅ **Simple CRUD**: Basic database operations  
✅ **Legacy code**: Existing sync codebase

## 🛠️ Commands Cheat Sheet

### Docker Commands

```bash
# Start everything
docker-compose up --build -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop everything
docker-compose down

# Clean up
docker-compose down -v --rmi all
```

### Helper Scripts

```bash
# Windows
docker-commands.bat build
docker-commands.bat up
docker-commands.bat benchmark
docker-commands.bat down

# Linux/Mac
./docker-commands.sh build
./docker-commands.sh up
./docker-commands.sh benchmark
./docker-commands.sh down
```

### Manual Testing

```bash
# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# Quick tests
curl "http://localhost:8003/benchmark/quart-io-test?delay=1.0&concurrent=10"
curl "http://localhost:8002/benchmark/flask-io-test?delay=1.0&concurrent=10"
```

## 🔍 Monitoring

```bash
# Container resource usage
docker stats io-benchmark-fastapi io-benchmark-flask io-benchmark-quart

# Logs for specific service
docker-compose logs -f quart-server

# Execute commands in container
docker-compose exec quart-server /bin/bash
```

## 🎯 Decision Matrix

Should you migrate to Quart/Hypercorn?

| Average Speedup | Recommendation                                 |
| --------------- | ---------------------------------------------- |
| **< 2x**        | ⚠️ Moderate benefit - evaluate case-by-case    |
| **2-5x**        | ✅ Good candidate - plan gradual migration     |
| **5-10x**       | ✅✅ Strong case - prioritize migration        |
| **> 10x**       | 🚀 Excellent - migrate critical endpoints ASAP |

## 📝 Migration Strategy

1. **Benchmark first** - Get baseline metrics
2. **Identify hot paths** - Find IO-heavy endpoints
3. **Start small** - Convert one endpoint
4. **Measure impact** - Compare before/after
5. **Expand gradually** - Convert more endpoints
6. **Monitor production** - Track real-world improvements

## 🐛 Troubleshooting

### Containers won't start

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Port conflicts

Edit `docker-compose.yml` and change port mappings

### Network issues

```bash
docker network prune
docker-compose up -d
```

### Performance issues

1. Increase Docker resources (Settings → Resources)
2. Reduce worker count in Dockerfiles
3. Close other applications

## 📚 Additional Resources

- **Quart**: https://quart.palletsprojects.com/
- **Hypercorn**: https://hypercorn.readthedocs.io/
- **Gunicorn**: https://docs.gunicorn.org/
- **FastAPI**: https://fastapi.tiangolo.com/

## ✅ Pre-flight Checklist

Before running benchmarks:

- [ ] Docker installed and running
- [ ] Port 8001-8003 available
- [ ] Sufficient disk space (~500MB)
- [ ] Sufficient memory (~500MB)
- [ ] Python 3.8+ installed (for benchmark script)
- [ ] `requests` package installed

## 🎉 Success Criteria

You've successfully completed the benchmark when you see:

1. ✅ All 3 containers healthy
2. ✅ Benchmark completes without errors
3. ✅ Results show clear speedup patterns
4. ✅ Higher concurrency = higher speedup
5. ✅ Async uses less CPU under load

## 🚀 Next Steps

1. **Run the benchmark** using Docker
2. **Analyze results** - Look for speedup patterns
3. **Identify candidates** - Find IO-heavy endpoints in your app
4. **Plan migration** - Start with highest-impact endpoints
5. **Test in staging** - Validate before production
6. **Deploy gradually** - Monitor and iterate

---

**Ready to quantify your async gains?**

```bash
cd 00_scripts/io_benchmark
docker-compose up --build -d && python benchmark_docker.py
```

🐳 **Production-ready. Reproducible. Realistic.**
