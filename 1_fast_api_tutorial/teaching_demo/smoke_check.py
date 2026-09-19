"""From the tutorial: `uv run --locked python teaching_demo/smoke_check.py`."""

import importlib
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient


def check_checkpoints():
    for number in range(1, 6):
        module = importlib.import_module(f"step{number:02d}")
        with TestClient(module.app) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert response.json() == {"message": "Hello, data scientists!"}
            assert client.get("/docs").status_code == 200
            schema = client.get("/openapi.json").json()
            assert schema["info"]["title"] == "FastAPI for Data Scientists"

            if number >= 2:
                assert client.get("/square/4").json() == {"result": 16}
                assert client.get("/square/banana").status_code == 422
                assert len(client.get("/items").json()) == 3
                assert client.get("/items?skip=1&limit=2").json() == [
                    {"id": 1, "name": "item-1"},
                    {"id": 2, "name": "item-2"},
                ]
                for query in ("skip=-1", "limit=0", "limit=11", "skip=banana"):
                    assert client.get(f"/items?{query}").status_code == 422

            if number >= 3:
                response = client.post("/predict", json={"features": [1, 2, 3]})
                assert response.status_code == 200
                assert response.json() == {
                    "prediction": 2.0,
                    "model": "demo-mean-v1",
                }
                for invalid in ({}, {"features": []}, {"features": ["banana"]},
                                {"features": [1] * 101}):
                    assert client.post("/predict", json=invalid).status_code == 422
                operation = schema["paths"]["/predict"]["post"]
                assert "requestBody" in operation
                assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("PredictionResponse")

            if number == 5:
                assert client.get("/jobs/missing").status_code == 404
                assert client.post("/jobs", json={"features": []}).status_code == 422
                response = client.get("/sample-image")
                assert response.status_code == 200
                assert response.headers["content-type"] == "image/png"
                assert response.content.startswith(b"\x89PNG\r\n\x1a\n")

        print(f"step{number:02d}: routes, validation and documentation passed")

    # Exercise the failure branch without adding a magic student-facing input.
    with patch.object(module.time, "sleep"), patch.object(
        module, "predict", side_effect=RuntimeError("Simulated model failure")
    ):
        module.run_prediction_job("failure-check", module.PredictionRequest(features=[1]))
    assert module.jobs["failure-check"]["status"] == "failed"
    assert "error" in module.jobs["failure-check"]
    del module.jobs["failure-check"]
    print("step05: worker failure is recorded")


def check_http_timing():
    # TestClient waits for background work to finish; use a real HTTP server.
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

    with tempfile.TemporaryFile(mode="w+") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "step05:app", "--host", "127.0.0.1",
             "--port", str(port), "--log-level", "warning"],
            cwd=Path(__file__).parent,
            stdout=log,
            stderr=log,
        )
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=10) as client:
                deadline = time.monotonic() + 10
                while True:
                    try:
                        if client.get("/").status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    if process.poll() is not None or time.monotonic() > deadline:
                        log.seek(0)
                        raise AssertionError(f"Demo server did not start: {log.read()}")
                    time.sleep(0.1)

                payload = {"features": [1, 2, 3]}
                started = time.monotonic()
                response = client.post("/predict-slow", json=payload)
                slow_seconds = time.monotonic() - started
                assert response.status_code == 200
                assert response.json()["prediction"] == 2.0
                assert slow_seconds >= 4.8, slow_seconds

                started = time.monotonic()
                response = client.post("/jobs", json=payload)
                ack_seconds = time.monotonic() - started
                assert response.status_code == 202
                assert response.json()["status"] == "queued"
                assert ack_seconds < 2, ack_seconds
                job_id = response.json()["job_id"]
                response = client.get(f"/jobs/{job_id}")
                assert response.json()["status"] in ("queued", "running")
                assert client.get("/").status_code == 200

                deadline = time.monotonic() + 10
                while response.json()["status"] in ("queued", "running"):
                    assert time.monotonic() < deadline, response.text
                    time.sleep(0.1)
                    response = client.get(f"/jobs/{job_id}")
                assert response.json()["status"] == "succeeded"
                assert response.json()["result"] == {
                    "prediction": 2.0, "model": "demo-mean-v1"
                }
                print(f"HTTP: slow response {slow_seconds:.2f}s; 202 acknowledgement {ack_seconds:.3f}s; polling succeeded")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    check_checkpoints()
    check_http_timing()
    print("All smoke checks passed.")
