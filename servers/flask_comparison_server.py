"""
Flask Comparison Server for IO Benchmark
This is a minimal Flask app to compare sync performance against Quart
"""

import time

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuration
FASTAPI_BASE_URL = "http://localhost:8001"


@app.route("/")
def root():
    """Health check"""
    return jsonify(
        {"status": "ok", "message": "Flask Comparison Server", "type": "sync"}
    )


@app.route("/benchmark/flask-io-test")
def flask_io_test():
    """
    Flask endpoint that makes synchronous calls to the FastAPI test server.
    This demonstrates blocking IO behavior.

    Query params:
        delay: IO operation delay in seconds (default 1.0)
        concurrent: Number of sequential calls to make (default 1)
    """
    delay = float(request.args.get("delay", 1.0))
    concurrent = int(request.args.get("concurrent", 1))

    # Validate parameters
    if delay < 0.1 or delay > 10.0:
        return jsonify({"error": "delay must be between 0.1 and 10.0"}), 400

    if concurrent < 1 or concurrent > 100:
        return jsonify({"error": "concurrent must be between 1 and 100"}), 400

    start_time = time.time()
    results: list[dict[str, str | int | float]] = []
    errors: list[dict[str, str | float]] = []

    # Make synchronous requests - these will block!
    for i in range(concurrent):
        request_start = time.time()
        try:
            response = requests.get(
                f"{FASTAPI_BASE_URL}/slow-io",
                params={"delay": delay, "request_id": f"flask-req-{i}"},
                timeout=delay + 5,
            )
            request_duration = time.time() - request_start

            if response.status_code == 200:
                results.append(
                    {
                        "request_id": i,
                        "status": "success",
                        "duration": request_duration,
                        "data": response.json(),
                    }
                )
            else:
                errors.append(
                    {"request_id": i, "error": f"HTTP {response.status_code}"}
                )
        except requests.RequestException as e:
            request_duration = time.time() - request_start
            errors.append(
                {"request_id": i, "error": str(e), "duration": request_duration}
            )

    total_duration = time.time() - start_time

    return jsonify(
        {
            "server_type": "flask_sync",
            "test_params": {"delay": delay, "concurrent_requests": concurrent},
            "timing": {
                "total_duration": total_duration,
                "expected_duration_sync": delay * concurrent,
                "requests_per_second": (
                    concurrent / total_duration if total_duration > 0 else 0
                ),
            },
            "results": {
                "successful": len(results),
                "failed": len(errors),
                "total": concurrent,
            },
            "details": results[:5],  # Only return first 5 for brevity
            "errors": errors[:5] if errors else [],
            "note": "Flask executes requests sequentially (blocking IO)",
        }
    )


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "type": "flask_sync",
            "timestamp": time.time(),
            "fastapi_server": FASTAPI_BASE_URL,
        }
    )


def main():
    """Entry point for the Flask server"""
    print("Starting Flask Comparison Server...")
    print("Server will run on http://localhost:8002")
    print("\nAvailable endpoints:")
    print("  GET /benchmark/flask-io-test?delay=1.0&concurrent=5")
    print("  GET /health")
    print("\nNote: Make sure FastAPI server is running on port 8001")

    app.run(
        host="0.0.0.0",
        port=8002,
        debug=False,
        threaded=True,  # Enable threading to handle concurrent benchmark requests
    )


if __name__ == "__main__":
    main()
