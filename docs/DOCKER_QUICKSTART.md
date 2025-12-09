# Docker Quick Start - 3 Commands

Get production benchmark results in under 5 minutes.

## TL;DR

```bash
cd 00_scripts/io_benchmark

# 1. Start everything
docker-compose up --build -d

# 2. Wait ~30 seconds for health checks, then run benchmark
python benchmark_docker.py

# 3. Stop everything
docker-compose down
```

## Detailed Steps

### Step 1: Build and Start (2-3 minutes)

```bash
docker-compose up --build -d
```

This will:

- ✅ Build 3 Docker images (FastAPI, Flask/Gunicorn, Quart/Hypercorn)
- ✅ Start all containers in detached mode
- ✅ Set up internal Docker network
- ✅ Run health checks

### Step 2: Wait for Services

```bash
# Watch containers start
docker-compose ps

# Or watch logs
docker-compose logs -f
```

Wait until you see:

```
io-benchmark-fastapi   ... Up (healthy)
io-benchmark-flask     ... Up (healthy)
io-benchmark-quart     ... Up (healthy)
```

### Step 3: Run Benchmark (30-60 seconds)

```bash
python benchmark_docker.py
```

You'll see output like:

```
Production IO Benchmark: Quart/Hypercorn (ASGI) vs Flask/Gunicorn (WSGI)

Average Speedup: 12.34x
Maximum Speedup: 38.59x

🎉 Excellent results! Quart/Hypercorn provides significant performance benefits
```

### Step 4: Stop Services

```bash
docker-compose down
```

## Using Helper Scripts (Windows)

```cmd
docker-commands.bat build
docker-commands.bat up
docker-commands.bat benchmark
docker-commands.bat down
```

## Using Helper Scripts (Linux/Mac)

```bash
./docker-commands.sh build
./docker-commands.sh up
./docker-commands.sh benchmark
./docker-commands.sh down
```

## Quick Commands Reference

| Task               | Command                            |
| ------------------ | ---------------------------------- |
| **Build**          | `docker-compose build`             |
| **Start**          | `docker-compose up -d`             |
| **Stop**           | `docker-compose down`              |
| **View Logs**      | `docker-compose logs -f`           |
| **Status**         | `docker-compose ps`                |
| **Benchmark**      | `python benchmark_docker.py`       |
| **Test Endpoints** | See below                          |
| **Resource Usage** | `docker stats`                     |
| **Clean All**      | `docker-compose down -v --rmi all` |

## Manual Endpoint Testing

```bash
# Test FastAPI (should return in ~1s)
curl "http://localhost:8001/slow-io?delay=1.0"

# Test Flask/Gunicorn (10 sequential requests = ~10s)
curl "http://localhost:8002/benchmark/flask-io-test?delay=1.0&concurrent=10"

# Test Quart/Hypercorn (10 concurrent requests = ~1s)
curl "http://localhost:8003/benchmark/quart-io-test?delay=1.0&concurrent=10"

# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## What Gets Benchmarked?

| Scenario               | Description             | Expected Result     |
| ---------------------- | ----------------------- | ------------------- |
| **Baseline**           | 1 request, 0.5s delay   | Similar performance |
| **Low Concurrency**    | 5 requests, 1s delay    | Quart ~5x faster    |
| **Medium Concurrency** | 10 requests, 1s delay   | Quart ~10x faster   |
| **High Concurrency**   | 20 requests, 0.5s delay | Quart ~20x faster   |
| **Stress Test**        | 50 requests, 0.3s delay | Quart ~50x faster   |

## Troubleshooting

### Containers won't start

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use

```bash
# Find what's using the ports
netstat -ano | findstr "800[123]"    # Windows
lsof -i :8001                        # Mac/Linux

# Kill the process or change ports in docker-compose.yml
```

### Health checks failing

```bash
# Check individual container logs
docker-compose logs fastapi-server
docker-compose logs flask-server
docker-compose logs quart-server
```

### Benchmark script errors

```bash
# Make sure containers are healthy first
docker-compose ps

# Check network connectivity
docker network inspect io_benchmark_benchmark-network
```

## Resource Requirements

- **Disk**: ~500MB for images
- **Memory**: ~500MB total (running)
- **CPU**: Minimal when idle
- **Time**:
  - Build: 2-3 minutes (first time)
  - Benchmark: 30-60 seconds
  - Total: ~5 minutes

## Next Steps

After running the benchmark:

1. **Review Results**: Check the speedup factors
2. **Analyze Patterns**: Higher concurrency = bigger gains
3. **Consider Migration**: If avg speedup > 5x, strong case for async
4. **Test with Real Data**: Replace FastAPI test server with your actual APIs
5. **Monitor Production**: Deploy and measure real-world improvements

## Full Documentation

- **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Complete Docker guide
- **[README.md](README.md)** - Project overview
- **Production deployment** - See DOCKER_GUIDE.md for details

---

**Ready? Run these 3 commands:** 🐳

```bash
docker-compose up --build -d
python benchmark_docker.py
docker-compose down
```
