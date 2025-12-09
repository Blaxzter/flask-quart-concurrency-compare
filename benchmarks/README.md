# Benchmark Scripts

This directory contains different benchmark scripts to test various aspects of async vs sync performance.

## 📊 Benchmark Types

### 1. `benchmark_docker.py` - Internal Concurrency Test

**What it tests**: How well each server handles making multiple external API calls within a single request.

**Scenario**:

- 1 client request → Server makes N concurrent/sequential external calls
- Flask: Makes N sequential blocking calls (takes N × delay seconds)
- Quart: Makes N concurrent async calls (takes ~delay seconds)

**Use case**: When one user request needs to aggregate data from multiple sources.

**Expected results**: Quart 5-50x faster depending on N

```bash
python benchmarks/benchmark_docker.py
```

### 2. `benchmark_concurrent_clients.py` - Real Concurrency Test ⭐ **RECOMMENDED**

**What it tests**: How many simultaneous client requests each server can handle.

**Scenario**:

- N clients → Each makes 1 request with 1 external call
- Tests true concurrent user handling
- Shows Gunicorn worker/thread limits vs Hypercorn event loop

**Use case**: Production load - multiple users hitting your API at the same time.

**Expected results**:

- Gunicorn limited to ~8 concurrent (4 workers × 2 threads)
- Hypercorn handles 100s-1000s concurrent
- Quart 2-5x better throughput

```bash
python benchmarks/benchmark_concurrent_clients.py
```

### 3. `benchmark.py` - Development Server Test

**What it tests**: Same as `benchmark_docker.py` but with dev servers (not production).

```bash
# Start dev servers first
python servers/fastapi_server.py      # Terminal 1
python servers/flask_comparison_server.py  # Terminal 2
python benchmarks/benchmark.py        # Terminal 3
```

### 4. `quick_test.py` - Health Check

**What it tests**: Verifies all servers are running and responding.

```bash
python benchmarks/quick_test.py
```

## 🎯 Which Benchmark Should You Use?

### For Production Decision Making

Use **`benchmark_concurrent_clients.py`** - it shows real-world concurrent user handling.

### For Understanding Internal Async Benefits

Use **`benchmark_docker.py`** - it shows how async helps when one request needs multiple external calls.

### For Development Testing

Use **`benchmark.py`** - quick tests without Docker overhead.

## 📈 Understanding the Difference

### Scenario 1: Internal Concurrency (`benchmark_docker.py`)

```
Single User Request Flow:

Flask/Gunicorn (Sync):
User → [Call API 1] → wait → [Call API 2] → wait → [Call API 3] → wait
Total: 3 seconds (sequential)

Quart/Hypercorn (Async):
User → [Call API 1, API 2, API 3] → all wait concurrently
Total: 1 second (parallel)

Speedup: 3x
```

### Scenario 2: Concurrent Clients (`benchmark_concurrent_clients.py`)

```
Multiple Users Hitting Server:

Flask/Gunicorn (4 workers, 2 threads = 8 concurrent max):
User 1-8  → Handled immediately
User 9-16 → Queued, waiting for worker
User 17+  → Queued, longer wait

Quart/Hypercorn (Event loop, thousands concurrent):
User 1-100  → All handled concurrently
User 101+   → All handled concurrently
No queuing within reasonable limits

Throughput Improvement: 2-5x
```

## 🚀 Quick Start

### Production Docker Benchmark (Concurrent Clients)

```bash
# Make sure containers are running
docker-compose ps

# Run the concurrent client test
python benchmarks/benchmark_concurrent_clients.py
```

### Production Docker Benchmark (Internal Concurrency)

```bash
python benchmarks/benchmark_docker.py
```

## 📊 Example Output

### Concurrent Clients Test

```
Scenario 3: Medium Load (20 concurrent clients)
  20 clients, each making 1 external call

  Results:
    Metric                         Flask/Gunicorn            Quart/Hypercorn            Improvement
    -----------------------------------------------------------------------------------------------
    Total Duration                      2.876s                     0.623s                 4.62x
    Avg Response Time                   2.234s                     0.543s                 4.11x
    Throughput (req/s)                   6.95                      32.10                  4.62x

  🚀 Excellent! Quart handles significantly more concurrent clients
```

### Internal Concurrency Test

```
Scenario 3: Medium Concurrency (10 requests)
  Results:
    Metric                         Flask/Gunicorn            Quart/Hypercorn            Improvement
    -----------------------------------------------------------------------------------------------
    Total Duration                     10.234s                     1.156s                 8.85x
    Requests/sec                        0.98                       8.65                   8.85x

  🚀 Excellent! Async provides major speedup
```

## 🎓 Key Takeaways

1. **Concurrent Clients Test** = Real production scenario

   - Shows how many users can be served simultaneously
   - Gunicorn limited by worker × thread count
   - Hypercorn scales with event loop

2. **Internal Concurrency Test** = Async benefit within requests

   - Shows efficiency when one request makes multiple external calls
   - Async can parallelize these calls
   - Sync must do them sequentially

3. **Both are important!**
   - Concurrent clients = Server capacity
   - Internal concurrency = Request efficiency

## 🔧 Requirements

All benchmarks need:

- Docker containers running (for Docker benchmarks)
- Python 3.8+
- `aiohttp` and `requests` packages

Installed automatically with:

```bash
pip install -e ..
```

Or manually:

```bash
pip install aiohttp requests
```

## 📚 Further Reading

See parent directory documentation:

- `../docs/DOCKER_GUIDE.md` - Complete Docker setup
- `../docs/SUMMARY.md` - Full project overview
- `../README.md` - Quick start guide
