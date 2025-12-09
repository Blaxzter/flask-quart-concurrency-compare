"""
FastAPI Test Server for IO Benchmark
Simulates slow IO-bound operations like LLM calls or external API requests
"""

import asyncio
import logging
import time

from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI(title="IO Benchmark Test Server")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Simple gate to coordinate a "release all" style concurrency test.
concurrency_gate = asyncio.Event()
concurrency_gate.clear()
concurrency_lock = asyncio.Lock()
waiting_requests = 0
release_round = 1


class IOResponse(BaseModel):
    message: str
    delay: float
    timestamp: float
    request_id: str | None = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "IO Benchmark Test Server"}


@app.get("/slow-io", response_model=IOResponse)
async def slow_io_endpoint(
    delay: float = Query(default=1.0, ge=0.1, le=10.0, description="Delay in seconds"),
    request_id: str | None = Query(
        default=None, description="Optional request ID for tracking"
    ),
):
    """
    Simulates a slow IO-bound operation (like an LLM API call)

    Args:
        delay: Time to sleep in seconds (default 1.0, min 0.1, max 10.0)
        request_id: Optional identifier for tracking requests
    """

    # Simulate IO-bound operation (e.g., LLM API call)
    await asyncio.sleep(delay)

    return IOResponse(
        message=f"IO operation completed after {delay} seconds",
        delay=delay,
        timestamp=time.time(),
        request_id=request_id,
    )


@app.get("/slow-io-sync", response_model=IOResponse)
def slow_io_sync_endpoint(
    delay: float = Query(default=1.0, ge=0.1, le=10.0, description="Delay in seconds"),
    request_id: str | None = Query(
        default=None, description="Optional request ID for tracking"
    ),
):
    """
    Synchronous version - simulates blocking IO operation
    """
    # Simulate blocking IO operation
    time.sleep(delay)

    return IOResponse(
        message=f"Sync IO operation completed after {delay} seconds",
        delay=delay,
        timestamp=time.time(),
        request_id=request_id,
    )


@app.get("/concurrency/block")
async def concurrency_block(
    delay: float = Query(
        default=1.0, ge=0.0, le=30.0, description="Extra delay after release"
    ),
    request_id: str | None = Query(
        default=None, description="Optional request ID for tracking"
    ),
):
    """
    Queues up requests behind a shared gate. They only proceed once
    `/concurrency/release` is called, allowing easy measurement of how many
    concurrent requests the server can hold open.
    """
    global waiting_requests
    async with concurrency_lock:
        waiting_requests += 1
        current_round = release_round
        queued_at = waiting_requests

    logger.info(f"Queued request {waiting_requests} at round {current_round}")
    await concurrency_gate.wait()
    await asyncio.sleep(delay)
    logger.info(f"Request {request_id} released after {delay} seconds")

    async with concurrency_lock:
        waiting_requests -= 1
        remaining = waiting_requests

    return {
        "message": "Request released",
        "round": current_round,
        "slept_after_release": delay,
        "request_id": request_id,
        "queued_position": queued_at,
        "currently_waiting": remaining,
        "timestamp": time.time(),
    }


@app.post("/concurrency/release")
async def concurrency_release(
    reset_gate: bool = Query(
        default=True,
        description="Whether to reset the gate after releasing waiting requests",
    ),
    rearm_delay: float = Query(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="Optional delay before re-arming the gate",
    ),
):
    """
    Releases all currently blocked `/concurrency/block` requests.
    Optionally re-arms the gate so the next wave will block again.
    """
    global release_round
    async with concurrency_lock:
        snapshot_waiting = waiting_requests
        current_round = release_round
        concurrency_gate.set()
        released_at = time.time()

    logger.info(f"Released {snapshot_waiting} requests at round {current_round}")

    if reset_gate:
        if rearm_delay:
            await asyncio.sleep(rearm_delay)
        concurrency_gate.clear()
        async with concurrency_lock:
            release_round += 1

    return {
        "message": "Released waiting requests",
        "round": current_round,
        "released_waiting": snapshot_waiting,
        "gate_rearmed": reset_gate,
        "rearm_delay": rearm_delay if reset_gate else 0.0,
        "timestamp": released_at,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "endpoints": [
            "/slow-io",
            "/slow-io-sync",
            "/concurrency/block",
            "/concurrency/release",
            "/health",
        ],
    }


def main():
    """Entry point for the FastAPI server"""
    import uvicorn

    logger.info("Starting FastAPI IO Benchmark Server...")
    logger.info("Server will run on http://localhost:8001")
    logger.info("\nAvailable endpoints:")
    logger.info("  GET /slow-io?delay=1.0             - Async IO simulation")
    logger.info("  GET /slow-io-sync?delay=1.0        - Sync IO simulation")
    logger.info("  GET /concurrency/block             - Hold requests until release")
    logger.info("  POST /concurrency/release          - Release blocked requests")
    logger.info("  GET /health                        - Health check")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")


if __name__ == "__main__":
    main()
