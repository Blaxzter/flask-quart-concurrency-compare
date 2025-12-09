"""
Automated Benchmark Script
Compares Quart (async) vs Flask (sync) performance for IO-bound operations
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


def run_benchmark(url: str, params: dict, name: str) -> BenchmarkResult | None:
    """Run a single benchmark test"""
    print(f"  Running: {name}...")

    try:
        response = requests.get(url, params=params, timeout=60)

        if response.status_code == 200:
            data = response.json()
            return BenchmarkResult(
                name=name,
                total_duration=data["timing"]["total_duration"],
                requests_per_second=data["timing"]["requests_per_second"],
                successful_requests=data["results"]["successful"],
                failed_requests=data["results"]["failed"],
                expected_duration=params["delay"] * params["concurrent"],
            )
        else:
            print(f"    Error: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def print_comparison(
    quart_result: BenchmarkResult | None, flask_result: BenchmarkResult | None
):
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
        f"    {'Metric':<25} {'Flask (sync)':<20} {'Quart (async)':<20} {'Improvement':<15}"
    )
    print(f"    {'-' * 80}")
    print(
        f"    {'Total Duration':<25} {flask_result.total_duration:>10.3f}s {quart_result.total_duration:>18.3f}s {speedup:>12.2f}x"
    )
    print(
        f"    {'Requests/sec':<25} {flask_result.requests_per_second:>10.2f} {quart_result.requests_per_second:>22.2f} {throughput_improvement:>12.2f}x"
    )
    print(
        f"    {'Successful Requests':<25} {flask_result.successful_requests:>10} {quart_result.successful_requests:>22}"
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
    print("=" * 80)
    print("IO-Bound Performance Benchmark: Quart (Async) vs Flask (Sync)")
    print("=" * 80)

    # Configuration
    QUART_URL = "http://localhost:5000/oapi/benchmark/quart-io-test"
    FLASK_URL = "http://localhost:8002/benchmark/flask-io-test"

    # Check if servers are running
    print("\n1. Checking server availability...")
    try:
        requests.get("http://localhost:8001/health", timeout=2)
        print("   ✅ FastAPI test server (port 8001) is running")
    except Exception:
        print("   ❌ FastAPI test server not running!")
        print("   Start it with: python 00_scripts/io_benchmark/fastapi_server.py")
        return

    try:
        requests.get("http://localhost:5000/oapi/health", timeout=2)
        print("   ✅ Quart server (port 5000) is running")
    except Exception:
        print("   ❌ Quart server not running!")
        print("   Start your main Respeak backend application")
        return

    try:
        requests.get("http://localhost:8002/health", timeout=2)
        print("   ✅ Flask comparison server (port 8002) is running")
    except Exception:
        print("   ❌ Flask comparison server not running!")
        print(
            "   Start it with: python 00_scripts/io_benchmark/flask_comparison_server.py"
        )
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
    ]

    print("\n2. Running benchmark scenarios...")
    print("=" * 80)

    all_speedups = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario['name']}")
        print(f"  {scenario['description']}")
        print(
            f"  Parameters: delay={scenario['params']['delay']}s, concurrent={scenario['params']['concurrent']}"
        )

        # Run Flask test
        flask_result = run_benchmark(
            FLASK_URL, scenario["params"], f"Flask - {scenario['name']}"
        )

        # Run Quart test
        quart_result = run_benchmark(
            QUART_URL, scenario["params"], f"Quart - {scenario['name']}"
        )

        # Compare results
        print_comparison(quart_result, flask_result)

        if quart_result and flask_result:
            speedup = flask_result.total_duration / quart_result.total_duration
            all_speedups.append(speedup)

        print("\n" + "-" * 80)

    # Overall summary
    print("\n3. Overall Summary")
    print("=" * 80)

    if all_speedups:
        avg_speedup = statistics.mean(all_speedups)
        max_speedup = max(all_speedups)
        min_speedup = min(all_speedups)

        print(f"  Average Speedup: {avg_speedup:.2f}x")
        print(f"  Maximum Speedup: {max_speedup:.2f}x")
        print(f"  Minimum Speedup: {min_speedup:.2f}x")

        print("\n  Key Insights:")
        print("  • Async (Quart) excels at concurrent IO-bound operations")
        print("  • Speedup increases with concurrency level")
        print("  • Ideal for: LLM APIs, external services, database queries")
        print("  • Lower CPU usage and better resource utilization")

        if avg_speedup >= 5:
            print(
                "\n  🎉 Excellent results! Quart provides significant performance benefits"
            )
        elif avg_speedup >= 2:
            print("\n  ✅ Good results! Quart shows clear performance advantages")
        else:
            print("\n  👍 Results as expected for mixed concurrency levels")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
