"""Benchmark one local Uvicorn process over real loopback HTTP, without paid inference."""

import json
import math
import os
import platform
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {**os.environ, "RAG_REQUESTS_PER_MINUTE": "10000", "RAG_API_KEY": ""}
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--no-access-log",
        "--log-level",
        "warning",
    ]
    process = subprocess.Popen(
        command, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    payload = {"question": "How does token bucket rate limiting allow bursts?"}
    try:
        with httpx.Client(
            base_url=f"http://127.0.0.1:{port}", timeout=20, trust_env=False
        ) as client:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("API process exited before readiness")
                try:
                    if client.get("/ready").status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(0.05)
            else:
                raise RuntimeError("API did not become ready")
            results = {}
            for path in ["/ask", "/agent"]:
                for _ in range(5):
                    client.post(path, json=payload).raise_for_status()
                samples = []
                for _ in range(100):
                    start = time.perf_counter()
                    response = client.post(path, json=payload)
                    response.raise_for_status()
                    samples.append((time.perf_counter() - start) * 1000)
                samples.sort()
                results[path] = {
                    "requests": len(samples),
                    "p50_ms": statistics.median(samples),
                    "p95_ms": samples[math.ceil(0.95 * len(samples)) - 1],
                    "max_ms": max(samples),
                }
            report = {
                "transport": "loopback HTTP, persistent client, one Uvicorn worker",
                "concurrency": 1,
                "warmup_per_endpoint": 5,
                "python": platform.python_version(),
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
                "provider_calls": 0,
                "provider_cost_usd": 0,
                "index": client.get("/ready").json(),
                "results": results,
                "scope": "Tiny corpus, repeated query; not a production load or LLM benchmark",
            }
            path = ROOT / "reports/latency.json"
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2))
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
