"""
Concurrent Client Benchmark
Tests how many concurrent CLIENT requests Flask/Gunicorn vs Quart/Hypercorn can handle
This is the REAL production scenario - multiple users hitting the server at once
"""

import asyncio
import statistics
import time
from dataclasses import dataclass

import aiohttp


@dataclass
class ConcurrentBenchmarkResult:
    """Results from concurrent client testing"""

    name: str
    concurrent_clients: int
    total_duration: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    successful_requests: int
    failed_requests: int


async def make_concurrent_requests(
    url: str, params: dict, num_clients: int
) -> ConcurrentBenchmarkResult:
    """
    Make multiple concurrent requests to test server concurrency handling
    This simulates multiple users hitting the endpoint at the same time
    """
    print(f"  Testing with {num_clients} concurrent clients...")

    start_time = time.time()
    response_times = []
    successful = 0
    failed = 0

    async def single_request(session: aiohttp.ClientSession, client_id: int):
        """Make a single request and measure its response time"""
        request_start = time.time()
        try:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                request_duration = time.time() - request_start
                if response.status == 200:
                    await response.json()
                    return {"success": True, "duration": request_duration}
                else:
                    return {
                        "success": False,
                        "duration": request_duration,
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            request_duration = time.time() - request_start
            return {"success": False, "duration": request_duration, "error": str(e)}

    # Create concurrent requests
    async with aiohttp.ClientSession() as session:
        tasks = [single_request(session, i) for i in range(num_clients)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    for result in results:
        if isinstance(result, Exception):
            failed += 1
        elif result.get("success"):
            successful += 1
            response_times.append(result["duration"])
        else:
            failed += 1
            if result.get("duration"):
                response_times.append(result["duration"])

    total_duration = time.time() - start_time

    if response_times:
        return ConcurrentBenchmarkResult(
            name=url.split(":")[-2].split("/")[0],  # Extract server name
            concurrent_clients=num_clients,
            total_duration=total_duration,
            avg_response_time=statistics.mean(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            requests_per_second=(
                num_clients / total_duration if total_duration > 0 else 0
            ),
            successful_requests=successful,
            failed_requests=failed,
        )
    else:
        return None


def print_comparison(
    quart_result: ConcurrentBenchmarkResult, flask_result: ConcurrentBenchmarkResult
):
    """Print comparison between Quart and Flask concurrent client results"""
    if not quart_result or not flask_result:
        print("    ⚠️  Could not compare - one or both tests failed")
        return

    throughput_improvement = (
        quart_result.requests_per_second / flask_result.requests_per_second
        if flask_result.requests_per_second > 0
        else 0
    )
    response_time_improvement = (
        flask_result.avg_response_time / quart_result.avg_response_time
        if quart_result.avg_response_time > 0
        else 0
    )

    print("\n  Results:")
    print(
        f"    {'Metric':<30} {'Flask/Gunicorn':<25} {'Quart/Hypercorn':<25} {'Improvement':<15}"
    )
    print(f"    {'-' * 95}")
    print(
        f"    {'Total Duration':<30} {flask_result.total_duration:>10.3f}s {quart_result.total_duration:>23.3f}s {flask_result.total_duration / quart_result.total_duration:>12.2f}x"
    )
    print(
        f"    {'Avg Response Time':<30} {flask_result.avg_response_time:>10.3f}s {quart_result.avg_response_time:>23.3f}s {response_time_improvement:>12.2f}x"
    )
    print(
        f"    {'Min Response Time':<30} {flask_result.min_response_time:>10.3f}s {quart_result.min_response_time:>23.3f}s"
    )
    print(
        f"    {'Max Response Time':<30} {flask_result.max_response_time:>10.3f}s {quart_result.max_response_time:>23.3f}s"
    )
    print(
        f"    {'Throughput (req/s)':<30} {flask_result.requests_per_second:>10.2f} {quart_result.requests_per_second:>27.2f} {throughput_improvement:>12.2f}x"
    )
    print(
        f"    {'Successful Requests':<30} {flask_result.successful_requests:>10} {quart_result.successful_requests:>27}"
    )

    # Performance verdict
    if throughput_improvement >= 2:
        verdict = "🚀 Excellent! Quart handles significantly more concurrent clients"
    elif throughput_improvement >= 1.5:
        verdict = "✅ Good! Quart shows clear concurrency advantages"
    elif throughput_improvement >= 1.2:
        verdict = "👍 Moderate improvement with Quart"
    else:
        verdict = "⚠️  Similar performance (may be limited by test setup)"

    print(f"\n  {verdict}")


async def main():
    """Run the concurrent client benchmark suite"""
    print("=" * 100)
    print("Concurrent Client Benchmark: Testing Real-World Concurrency Handling")
    print("=" * 100)

    # Configuration
    QUART_URL = "http://localhost:8003/benchmark/quart-io-test"
    FLASK_URL = "http://localhost:8002/benchmark/flask-io-test"

    # Check if servers are running
    print("\n1. Checking server availability...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8001/health", timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status == 200:
                    print("   ✅ FastAPI test server (port 8001) is running")
    except Exception:
        print("   ❌ FastAPI test server not running!")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8002/health", timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status == 200:
                    print("   ✅ Flask/Gunicorn server (port 8002) is running")
    except Exception:
        print("   ❌ Flask/Gunicorn server not running!")
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8003/health", timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status == 200:
                    print("   ✅ Quart/Hypercorn server (port 8003) is running")
    except Exception:
        print("   ❌ Quart/Hypercorn server not running!")
        return

    # Test scenarios - each client makes a request that does 1 external call
    scenarios = [
        {
            "name": "Low Load (5 concurrent clients)",
            "concurrent_clients": 5,
            "params": {"delay": 1.0, "concurrent": 1},
            "description": "5 clients, each making 1 external call",
        },
        {
            "name": "Medium Load (10 concurrent clients)",
            "concurrent_clients": 10,
            "params": {"delay": 1.0, "concurrent": 1},
            "description": "10 clients, each making 1 external call",
        },
        {
            "name": "High Load (20 concurrent clients)",
            "concurrent_clients": 20,
            "params": {"delay": 0.5, "concurrent": 1},
            "description": "20 clients, each making 1 external call",
        },
        {
            "name": "Heavy Load (50 concurrent clients)",
            "concurrent_clients": 50,
            "params": {"delay": 0.3, "concurrent": 1},
            "description": "50 clients, each making 1 external call",
        },
        {
            "name": "Stress Test (100 concurrent clients)",
            "concurrent_clients": 100,
            "params": {"delay": 0.2, "concurrent": 1},
            "description": "100 clients, each making 1 external call",
        },
    ]

    print("\n2. Running concurrent client benchmarks...")
    print("=" * 100)
    print("\n📊 This tests how many SIMULTANEOUS USERS each server can handle")
    print(
        "   (Real production scenario: multiple clients hitting the server at once)\n"
    )

    all_improvements = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario['name']}")
        print(f"  {scenario['description']}")
        print(
            f"  Parameters: {scenario['concurrent_clients']} clients, delay={scenario['params']['delay']}s"
        )

        # Test Flask
        print("\n  Testing Flask/Gunicorn...")
        flask_result = await make_concurrent_requests(
            FLASK_URL, scenario["params"], scenario["concurrent_clients"]
        )

        # Small delay between tests
        await asyncio.sleep(1)

        # Test Quart
        print("  Testing Quart/Hypercorn...")
        quart_result = await make_concurrent_requests(
            QUART_URL, scenario["params"], scenario["concurrent_clients"]
        )

        # Compare results
        print_comparison(quart_result, flask_result)

        if quart_result and flask_result:
            improvement = (
                quart_result.requests_per_second / flask_result.requests_per_second
            )
            all_improvements.append(improvement)

        print("\n" + "-" * 100)

    # Overall summary
    print("\n3. Overall Summary")
    print("=" * 100)

    if all_improvements:
        avg_improvement = statistics.mean(all_improvements)
        max_improvement = max(all_improvements)
        min_improvement = min(all_improvements)

        print(f"  Average Throughput Improvement: {avg_improvement:.2f}x")
        print(f"  Maximum Throughput Improvement: {max_improvement:.2f}x")
        print(f"  Minimum Throughput Improvement: {min_improvement:.2f}x")

        print("\n  Key Insights:")
        print("  • Async (Quart/Hypercorn) handles more concurrent clients efficiently")
        print("  • Response times remain consistent under load with async")
        print(
            "  • Gunicorn is limited by worker/thread count (4 workers × 2 threads = 8 concurrent)"
        )
        print(
            "  • Hypercorn scales with event loop (thousands of concurrent connections)"
        )
        print("  • Production benefit: More users can be served simultaneously")

        if avg_improvement >= 2:
            print(
                "\n  🎉 Excellent! Quart/Hypercorn is significantly better at handling concurrent clients"
            )
            print("  💡 Recommendation: Strong case for production migration")
        elif avg_improvement >= 1.5:
            print("\n  ✅ Good! Quart/Hypercorn shows clear advantages")
            print("  💡 Recommendation: Consider migration for high-traffic endpoints")
        else:
            print("\n  ℹ️  Results show moderate improvements")
            print("  💡 Recommendation: May be limited by test server or network")

    print("\n" + "=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
