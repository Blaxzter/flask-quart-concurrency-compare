"""
Quick Test Script
Run this to verify all servers are working correctly before running full benchmark
"""

import argparse
import concurrent.futures
import time

import requests


def test_server(name: str, url: str, expected_status: int = 200) -> bool:
    """Test if a server is running and responding"""
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == expected_status:
            print(f"  ? {name} is running")
            return True
        else:
            print(f"  ? {name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ? {name} is not running (connection refused)")
        return False
    except Exception as e:
        print(f"  ? {name} error: {e}")
        return False


def probe_concurrency(
    base_url: str = "http://localhost:8001",
    start: int = 5,
    step: int = 20,
    max_concurrency: int = 500,
    block_delay: float = 0.05,
):
    """
    Gradually increase concurrent requests against the FastAPI concurrency gate
    until a failure occurs or max_concurrency is reached.
    """

    def call_block(request_id: int):
        return requests.get(
            f"{base_url}/concurrency/block",
            params={
                "delay": block_delay,
                "request_id": f"concurrency-test-{request_id}",
            },
            timeout=15,
        )

    def release_gate():
        print("Calling release gate")
        return requests.post(f"{base_url}/concurrency/release", timeout=5)

    print("\nProbing FastAPI concurrency gate...")
    print("(uses /concurrency/block and /concurrency/release endpoints)\n")

    for concurrency in range(start, max_concurrency + 1, step):
        print(f"  Trying {concurrency} concurrent blocked requests...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(call_block, i) for i in range(concurrency)]

            # Allow requests to queue up on the gate before releasing
            time.sleep(0.2)
            try:
                release_response = release_gate()
            except Exception as exc:
                print(f"  ? Release failed at {concurrency}: {exc}")
                break

            errors: list[str] = []
            for future in futures:
                try:
                    response = future.result(timeout=20)
                    if response.status_code != 200:
                        errors.append(f"HTTP {response.status_code}")
                except Exception as exc:
                    errors.append(str(exc))

            if errors:
                print(
                    f"  ? Failure at {concurrency} concurrent requests "
                    + f"(sample: {errors[:3]})"
                )
                break

            released_waiting = None
            try:
                response_json: dict[str, int | float | str] = release_response.json()
                released_waiting = response_json.get("released_waiting")
            except Exception:
                pass

            info = (
                f"released_waiting={released_waiting}"
                if released_waiting is not None
                else "release response OK"
            )
            print(f"  ? {concurrency} requests succeeded ({info})")
    else:
        print(f"\nReached max concurrency target ({max_concurrency}) without failures.")


def probe_sleep_window(
    base_url: str = "http://localhost:8001",
    target_sleep: float = 3.0,
    max_workers: int = 200,
):
    """
    Fire as many /slow-io requests as possible within `target_sleep` seconds.
    Each request sleeps for the remaining time in the window (clamped to the
    endpoint's allowed range) so they should all complete around the same time.
    """

    def call_sleep(request_id: int, delay: float):
        return requests.get(
            f"{base_url}/slow-io",
            params={"delay": delay, "request_id": f"sleep-probe-{request_id}"},
            timeout=delay + 5,
        )

    print("\nProbing FastAPI /slow-io sleep window...")
    print(
        f"(send requests for ~{target_sleep:.2f}s; each uses remaining time as delay; "
        f"max_workers={max_workers})\n"
    )

    start_time = time.monotonic()
    deadline = start_time + target_sleep
    pending: set[concurrent.futures.Future] = set()
    successes = 0
    failures: list[str] = []
    total_sent = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        while True:
            now = time.monotonic()
            elapsed = now - start_time
            if elapsed >= target_sleep:
                break

            # Use remaining window time as the delay; clamp to server bounds (0.1-10s)
            remaining = deadline - now
            delay = min(max(remaining, 0.1), 10.0)

            pending.add(executor.submit(call_sleep, total_sent, delay))
            total_sent += 1

            if len(pending) >= max_workers:
                done, pending = concurrent.futures.wait(
                    pending, return_when=concurrent.futures.FIRST_COMPLETED
                )
                for future in done:
                    try:
                        response = future.result()
                        if response.status_code == 200:
                            successes += 1
                        else:
                            failures.append(f"HTTP {response.status_code}")
                    except Exception as exc:
                        failures.append(str(exc))

        for future in concurrent.futures.as_completed(pending):
            try:
                response = future.result()
                if response.status_code == 200:
                    successes += 1
                else:
                    failures.append(f"HTTP {response.status_code}")
            except Exception as exc:
                failures.append(str(exc))

    dispatch_duration = time.monotonic() - start_time
    qps = total_sent / dispatch_duration if dispatch_duration else 0.0

    print(
        f"  Dispatched {total_sent} requests in {dispatch_duration:.2f}s (~{qps:.1f}/s)"
    )
    print(f"  {successes} succeeded; {len(failures)} failed")
    if failures:
        print(f"    Sample failures: {failures[:3]}")


def main():
    parser = argparse.ArgumentParser(description="Quick probe for comparison servers")
    parser.add_argument(
        "--server",
        choices=["fastapi", "flask", "quart", "all"],
        default="quart",
        help="Which server(s) to probe",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Override base URL when probing a single server (e.g., http://localhost:8002)",
    )
    args = parser.parse_args()

    server_map = {
        "fastapi": {
            "name": "FastAPI Test Server",
            "base_url": "http://localhost:8001",
        },
        "quart": {"name": "Quart Server", "base_url": "http://localhost:8003"},
        "flask": {
            "name": "Flask Comparison",
            "base_url": "http://localhost:8002",
        },
    }

    if args.server != "all" and args.base_url:
        server_map[args.server]["base_url"] = args.base_url.rstrip("/")

    targets = list(server_map.keys()) if args.server == "all" else [args.server]

    print("Quick Server Test")
    print("=" * 60)

    servers = [
        (
            server_map[key]["name"],
            f"{server_map[key]['base_url']}/health",
            key,
        )
        for key in targets
    ]

    print("\nChecking server availability...\n")

    results: list[bool] = []
    for name, url, _ in servers:
        result = test_server(name, url)
        results.append(result)

    print("\n" + "=" * 60)

    if results and all(results):
        print("? All selected servers are running!")
        print("\nYou can now run the full benchmark:")
        print("  python benchmark.py")
    else:
        print("??  Some servers are not running")
        print("\nTo start the test servers:")
        print("  Windows: start_servers.bat")
        print("  Linux/Mac: bash start_servers.sh")
        print("\nDon't forget to start your main Quart application!")

    # Run probes only for healthy targets
    for idx, (name, _, key) in enumerate(servers):
        if not results[idx]:
            print(f"\nSkipping probes for {name} because it is unavailable.")
            continue

        base_url = server_map[key]["base_url"]
        print(f"\nRunning probes against {name} at {base_url}")
        probe_concurrency(base_url=base_url)
        probe_sleep_window(base_url=base_url)

    print()


if __name__ == "__main__":
    main()
