"""
Quick Test Script
Run this to verify all servers are working correctly before running full benchmark
"""

import concurrent.futures
import time

import requests


def test_server(name: str, url: str, expected_status: int = 200) -> bool:
    """Test if a server is running and responding"""
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == expected_status:
            print(f"  ✅ {name} is running")
            return True
        else:
            print(f"  ❌ {name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ {name} is not running (connection refused)")
        return False
    except Exception as e:
        print(f"  ❌ {name} error: {e}")
        return False


def probe_fastapi_concurrency(
    base_url: str = "http://localhost:8001",
    start: int = 1,
    step: int = 1,
    max_concurrency: int = 50,
    block_delay: float = 0.05,
):
    """
    Gradually increase concurrent requests against the FastAPI concurrency gate
    until a failure occurs or max_concurrency is reached.
    """

    def call_block(request_id: int):
        print(f"Calling block with request_id {request_id}")
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
                print(f"  ❌ Release failed at {concurrency}: {exc}")
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
                    f"  ❌ Failure at {concurrency} concurrent requests "
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
            print(f"  ✅ {concurrency} requests succeeded ({info})")
    else:
        print(f"\nReached max concurrency target ({max_concurrency}) without failures.")


def main():
    print("Quick Server Test")
    print("=" * 60)

    servers = [
        ("FastAPI Test Server (port 8001)", "http://localhost:8001/health"),
        ("Quart Server (port 8003)", "http://localhost:8003/health"),
        ("Flask Comparison (port 8002)", "http://localhost:8002/health"),
    ]

    print("\nChecking server availability...\n")

    results: list[bool] = []
    for name, url in servers:
        result = test_server(name, url)
        results.append(result)

    print("\n" + "=" * 60)

    if all(results):
        print("✅ All servers are running!")
        print("\nYou can now run the full benchmark:")
        print("  python benchmark.py")
    else:
        print("⚠️  Some servers are not running")
        print("\nTo start the test servers:")
        print("  Windows: start_servers.bat")
        print("  Linux/Mac: bash start_servers.sh")
        print("\nDon't forget to start your main Quart application!")

    # Only run the concurrency probe if the FastAPI server is healthy
    if results and results[0]:
        probe_fastapi_concurrency()
    else:
        print("\nSkipping concurrency probe because FastAPI is unavailable.")

    print()


if __name__ == "__main__":
    main()
