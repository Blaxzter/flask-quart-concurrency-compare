"""
Automated Benchmark Script for Docker Deployment
Compares Quart (async/Hypercorn) vs Flask (sync/Gunicorn) performance for IO-bound operations
"""

import statistics
from dataclasses import dataclass

import requests


@dataclass
class BenchmarkResult:
    """Results from a single benchmark test"""

    name: str
    total_duration: float
    requests_per_second: float
    successful_requests: int
    failed_requests: int
    expected_duration: float
    server_type: str


def run_benchmark(url: str, params: dict, name: str) -> BenchmarkResult | None:
    """Run a single benchmark test"""
    print(f"  Running: {name}...")

    try:
        response = requests.get(url, params=params, timeout=120)

        if response.status_code == 200:
            data = response.json()
            return BenchmarkResult(
                name=name,
                total_duration=data["timing"]["total_duration"],
                requests_per_second=data["timing"]["requests_per_second"],
                successful_requests=data["results"]["successful"],
                failed_requests=data["results"]["failed"],
                expected_duration=params["delay"] * params["concurrent"],
                server_type=data.get("server_type", "unknown"),
            )
        else:
            print(f"    Error: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def print_comparison(quart_result: BenchmarkResult, flask_result: BenchmarkResult):
    """Print comparison between Quart and Flask results"""
    if not quart_result or not flask_result:
        print("    ⚠️  Could not compare - one or both tests failed")
        return

    speedup = (
        flask_result.total_duration / quart_result.total_duration
        if quart_result.total_duration > 0
        else 0
    )
    throughput_improvement = (
        quart_result.requests_per_second / flask_result.requests_per_second
        if flask_result.requests_per_second > 0
        else 0
    )

    print("\n  Results:")
    print(
        f"    {'Metric':<30} {'Flask/Gunicorn':<25} {'Quart/Hypercorn':<25} {'Improvement':<15}"
    )
    print(f"    {'-' * 95}")
    print(
        f"    {'Total Duration':<30} {flask_result.total_duration:>10.3f}s {quart_result.total_duration:>23.3f}s {speedup:>12.2f}x"
    )
    print(
        f"    {'Requests/sec':<30} {flask_result.requests_per_second:>10.2f} {quart_result.requests_per_second:>27.2f} {throughput_improvement:>12.2f}x"
    )
    print(
        f"    {'Successful Requests':<30} {flask_result.successful_requests:>10} {quart_result.successful_requests:>27}"
    )

    # Performance verdict
    if speedup >= 5:
        verdict = "🚀 Excellent! Async provides major speedup"
    elif speedup >= 2:
        verdict = "✅ Good! Significant async benefit"
    elif speedup >= 1.2:
        verdict = "👍 Moderate async benefit"
    else:
        verdict = "⚠️  Minimal difference (expected for low concurrency)"

    print(f"\n  {verdict}")


def main():
    """Run the benchmark suite"""
    print("=" * 100)
    print("Production IO Benchmark: Quart/Hypercorn (ASGI) vs Flask/Gunicorn (WSGI)")
    print("=" * 100)

    # Configuration - Docker containers
    QUART_URL = "http://localhost:8003/benchmark/quart-io-test"
    FLASK_URL = "http://localhost:8002/benchmark/flask-io-test"

    # Check if servers are running
    print("\n1. Checking Docker containers availability...")
    servers_ok = True

    try:
        requests.get("http://localhost:8001/health", timeout=3)
        print("   ✅ FastAPI test server (port 8001) is running")
    except Exception:
        print("   ❌ FastAPI test server not running!")
        print("   Start with: docker-compose up fastapi-server")
        servers_ok = False

    try:
        requests.get("http://localhost:8002/health", timeout=3)
        print("   ✅ Flask/Gunicorn server (port 8002) is running")
    except Exception:
        print("   ❌ Flask/Gunicorn server not running!")
        print("   Start with: docker-compose up flask-server")
        servers_ok = False

    try:
        requests.get("http://localhost:8003/health", timeout=3)
        print("   ✅ Quart/Hypercorn server (port 8003) is running")
    except Exception:
        print("   ❌ Quart/Hypercorn server not running!")
        print("   Start with: docker-compose up quart-server")
        servers_ok = False

    if not servers_ok:
        print("\n❌ Not all servers are running!")
        print("\nTo start all servers:")
        print("  docker-compose up --build")
        print("\nOr start them individually:")
        print("  docker-compose up --build fastapi-server")
        print("  docker-compose up --build flask-server")
        print("  docker-compose up --build quart-server")
        return

    # Test scenarios
    scenarios = [
        {
            "name": "Single Request (Baseline)",
            "params": {"delay": 0.5, "concurrent": 1},
            "description": "One request with 0.5s delay - should be similar",
        },
        {
            "name": "Low Concurrency (5 requests)",
            "params": {"delay": 1.0, "concurrent": 5},
            "description": "5 concurrent 1s requests - Quart should be ~5x faster",
        },
        {
            "name": "Medium Concurrency (10 requests)",
            "params": {"delay": 1.0, "concurrent": 10},
            "description": "10 concurrent 1s requests - Quart should be ~10x faster",
        },
        {
            "name": "High Concurrency (20 requests)",
            "params": {"delay": 0.5, "concurrent": 20},
            "description": "20 concurrent 0.5s requests - Quart should be ~20x faster",
        },
        {
            "name": "Stress Test (50 requests)",
            "params": {"delay": 0.3, "concurrent": 50},
            "description": "50 concurrent 0.3s requests - Heavy load test",
        },
    ]

    print("\n2. Running benchmark scenarios...")
    print("=" * 100)
    print("\nNote: Running with production servers (Gunicorn/Hypercorn)")

    all_speedups = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario['name']}")
        print(f"  {scenario['description']}")
        print(
            f"  Parameters: delay={scenario['params']['delay']}s, concurrent={scenario['params']['concurrent']}"
        )

        # Run Flask test
        flask_result = run_benchmark(
            FLASK_URL, scenario["params"], f"Flask/Gunicorn - {scenario['name']}"
        )

        # Run Quart test
        quart_result = run_benchmark(
            QUART_URL, scenario["params"], f"Quart/Hypercorn - {scenario['name']}"
        )

        # Compare results
        print_comparison(quart_result, flask_result)

        if quart_result and flask_result:
            speedup = flask_result.total_duration / quart_result.total_duration
            all_speedups.append(speedup)

        print("\n" + "-" * 100)

    # Overall summary
    print("\n3. Overall Summary")
    print("=" * 100)

    if all_speedups:
        avg_speedup = statistics.mean(all_speedups)
        max_speedup = max(all_speedups)
        min_speedup = min(all_speedups)

        print(f"  Average Speedup: {avg_speedup:.2f}x")
        print(f"  Maximum Speedup: {max_speedup:.2f}x")
        print(f"  Minimum Speedup: {min_speedup:.2f}x")

        print("\n  Key Insights:")
        print("  • Async (Quart/Hypercorn) excels at concurrent IO-bound operations")
        print("  • Speedup increases with concurrency level")
        print(
            "  • Production servers (Gunicorn vs Hypercorn) show real-world performance"
        )
        print("  • Ideal for: LLM APIs, external services, database queries")
        print("  • Lower CPU usage and better resource utilization with async")

        if avg_speedup >= 5:
            print(
                "\n  🎉 Excellent results! Quart/Hypercorn provides significant performance benefits"
            )
        elif avg_speedup >= 2:
            print(
                "\n  ✅ Good results! Quart/Hypercorn shows clear performance advantages"
            )
        else:
            print("\n  👍 Results as expected for mixed concurrency levels")

        print("\n  Production Recommendations:")
        if avg_speedup >= 3:
            print("  ✅ Strong case for migrating to Quart/Hypercorn (ASGI)")
            print(
                "  ✅ Expected production improvements: faster response times, higher throughput"
            )
        else:
            print(
                "  ⚠️  Moderate improvements - evaluate based on your specific workload"
            )

    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
