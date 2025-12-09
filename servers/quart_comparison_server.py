"""
Quart Comparison Server for IO Benchmark
This is a production-ready Quart app to compare async performance
"""

import asyncio
import time

import aiohttp
from quart import Quart, jsonify, request

app = Quart(__name__)

# Fix for Quart/Flask compatibility issue
app.config["PROVIDE_AUTOMATIC_OPTIONS"] = True

# Configuration
FASTAPI_BASE_URL = "http://fastapi-server:8001"


@app.route("/")
async def root():
    """Health check"""
    return jsonify(
        {"status": "ok", "message": "Quart Comparison Server", "type": "async"}
    )


@app.route("/benchmark/quart-io-test")
async def quart_io_test():
    """
    Quart endpoint that makes asynchronous calls to the FastAPI test server.
    This demonstrates non-blocking IO behavior and concurrent execution.

    Query params:
        delay: IO operation delay in seconds (default 1.0)
        concurrent: Number of concurrent calls to make (default 1)
    """
    # Get and validate parameters
    try:
        delay = float(request.args.get("delay", 1.0))
        concurrent = int(request.args.get("concurrent", 1))
    except ValueError:
        return jsonify({"error": "Invalid parameters"}), 400

    if delay < 0.1 or delay > 10.0:
        return jsonify({"error": "delay must be between 0.1 and 10.0"}), 400

    if concurrent < 1 or concurrent > 100:
        return jsonify({"error": "concurrent must be between 1 and 100"}), 400

    start_time = time.time()
    results: list[dict[str, str | int | float]] = []
    errors: list[dict[str, str | float]] = []

    async def make_request(session: aiohttp.ClientSession, request_id: int):
        """Make a single async request to the FastAPI server"""
        request_start = time.time()
        try:
            async with session.get(
                f"{FASTAPI_BASE_URL}/slow-io",
                params={"delay": delay, "request_id": f"quart-req-{request_id}"},
                timeout=aiohttp.ClientTimeout(total=delay + 10),
            ) as response:
                request_duration = time.time() - request_start

                if response.status == 200:
                    data = await response.json()
                    return {
                        "request_id": request_id,
                        "status": "success",
                        "duration": request_duration,
                        "data": data,
                    }
                else:
                    return {
                        "request_id": request_id,
                        "status": "error",
                        "error": f"HTTP {response.status}",
                        "duration": request_duration,
                    }
        except Exception as e:
            request_duration = time.time() - request_start
            return {
                "request_id": request_id,
                "status": "error",
                "error": str(e),
                "duration": request_duration,
            }

    # Make concurrent requests using aiohttp
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, i) for i in range(concurrent)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process responses
        for response in responses:
            if isinstance(response, Exception):
                errors.append({"error": str(response)})
            elif isinstance(response, dict) and response.get("status") == "success":
                results.append(response)
            else:
                errors.append(response)

    total_duration = time.time() - start_time

    return jsonify(
        {
            "server_type": "quart_async_hypercorn",
            "test_params": {"delay": delay, "concurrent_requests": concurrent},
            "timing": {
                "total_duration": total_duration,
                "expected_duration_async": delay,
                "expected_duration_sync": delay * concurrent,
                "speedup_factor": (
                    (delay * concurrent) / total_duration if total_duration > 0 else 0
                ),
                "requests_per_second": (
                    concurrent / total_duration if total_duration > 0 else 0
                ),
            },
            "results": {
                "successful": len(results),
                "failed": len(errors),
                "total": concurrent,
            },
            "details": results[:5],
            "errors": errors[:5] if errors else [],
            "note": "Quart with Hypercorn executes requests concurrently (non-blocking IO)",
        }
    )


@app.route("/health")
async def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "type": "quart_async",
            "server": "hypercorn",
            "timestamp": time.time(),
            "fastapi_server": FASTAPI_BASE_URL,
        }
    )


def main():
    """Entry point for the Quart server"""

    print("Starting Quart Comparison Server...")
    print("Server will run on http://localhost:8003")
    print("\nAvailable endpoints:")
    print("  GET /benchmark/quart-io-test?delay=1.0&concurrent=5")
    print("  GET /health")
    print("\nNote: Make sure FastAPI server is running on port 8001")
    print("\nRunning with Hypercorn (production ASGI server)")

    # For local testing without Docker
    import hypercorn.asyncio
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8003"]
    asyncio.run(hypercorn.asyncio.serve(app, config))


if __name__ == "__main__":
    main()
