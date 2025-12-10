"""
Flask Comparison Server for IO Benchmark
This is a minimal Flask app to compare sync performance against Quart
"""

import time
import threading

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuration
FASTAPI_BASE_URL = "http://localhost:8001"

# Shared gate for concurrency test (mirrors FastAPI endpoints)
concurrency_gate = threading.Event()
concurrency_gate.clear()
concurrency_lock = threading.Lock()
waiting_requests = 0
release_round = 1


@app.route("/")
def root():
    """Health check"""
    return jsonify(
        {"status": "ok", "message": "Flask Comparison Server", "type": "sync"}
    )


def _parse_bool_arg(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "t", "yes", "y", "on"}


@app.route("/slow-io")
def slow_io_endpoint():
    """Simulates slow IO (blocking sleep) to mirror FastAPI endpoint"""
    try:
        delay = float(request.args.get("delay", 1.0))
    except ValueError:
        return jsonify({"error": "delay must be a number"}), 400

    if delay < 0.1 or delay > 10.0:
        return jsonify({"error": "delay must be between 0.1 and 10.0"}), 400

    request_id = request.args.get("request_id")
    time.sleep(delay)

    return jsonify(
        {
            "message": f"IO operation completed after {delay} seconds",
            "delay": delay,
            "timestamp": time.time(),
            "request_id": request_id,
        }
    )


@app.route("/slow-io-sync")
def slow_io_sync_endpoint():
    """Alias of slow-io to match FastAPI's sync endpoint"""
    return slow_io_endpoint()


@app.route("/concurrency/block")
def concurrency_block():
    """
    Queue requests behind a shared gate until /concurrency/release is called.
    """
    global waiting_requests
    try:
        delay = float(request.args.get("delay", 1.0))
    except ValueError:
        return jsonify({"error": "delay must be a number"}), 400

    if delay < 0.0 or delay > 30.0:
        return jsonify({"error": "delay must be between 0.0 and 30.0"}), 400

    request_id = request.args.get("request_id")

    with concurrency_lock:
        waiting_requests += 1
        current_round = release_round
        queued_at = waiting_requests

    concurrency_gate.wait()  # Blocks until release endpoint sets the gate
    time.sleep(delay)

    with concurrency_lock:
        waiting_requests -= 1
        remaining = waiting_requests

    return jsonify(
        {
            "message": "Request released",
            "round": current_round,
            "slept_after_release": delay,
            "request_id": request_id,
            "queued_position": queued_at,
            "currently_waiting": remaining,
            "timestamp": time.time(),
        }
    )


@app.route("/concurrency/release", methods=["POST"])
def concurrency_release():
    """
    Release all blocked /concurrency/block requests. Optionally re-arm gate.
    """
    global release_round
    reset_gate = _parse_bool_arg(request.args.get("reset_gate"), True)
    try:
        rearm_delay = float(request.args.get("rearm_delay", 0.0))
    except ValueError:
        return jsonify({"error": "rearm_delay must be a number"}), 400

    if rearm_delay < 0.0 or rearm_delay > 5.0:
        return jsonify({"error": "rearm_delay must be between 0.0 and 5.0"}), 400

    with concurrency_lock:
        snapshot_waiting = waiting_requests
        current_round = release_round
        concurrency_gate.set()
        released_at = time.time()

    if reset_gate:
        if rearm_delay:
            time.sleep(rearm_delay)
        concurrency_gate.clear()
        with concurrency_lock:
            release_round += 1

    return jsonify(
        {
            "message": "Released waiting requests",
            "round": current_round,
            "released_waiting": snapshot_waiting,
            "gate_rearmed": reset_gate,
            "rearm_delay": rearm_delay if reset_gate else 0.0,
            "timestamp": released_at,
        }
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
            "endpoints": [
                "/slow-io",
                "/slow-io-sync",
                "/concurrency/block",
                "/concurrency/release",
                "/benchmark/flask-io-test",
                "/health",
            ],
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
