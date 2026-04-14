from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
AUTH_SHARED_SECRET = "local-dev-shared-secret"
AUTH_ISSUER = "api-testing-auth"
AUTH_AUDIENCE = "api-testing-api"
TEST_RESET_API_KEY = "demo-reset-key"


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _wait_for_server(base_url: str, process: subprocess.Popen[str], timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout is not None else ""
            raise RuntimeError(f"server stopped before startup.\n{output}".strip())

        try:
            response = httpx.get(f"{base_url}/health", timeout=1.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_error = exc

        time.sleep(0.2)

    raise RuntimeError(f"Timed out waiting for server {base_url}. Last error: {last_error}")


def _start_service(module: str, port: int, extra_env: dict[str, str]) -> subprocess.Popen[str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{ROOT}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(ROOT)
    env.update(extra_env)
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            module,
            "--host",
            HOST,
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _stop_process(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _fetch_token(auth_base_url: str, username: str, password: str) -> str:
    response = httpx.post(
        f"{auth_base_url}/oauth/token",
        json={"username": username, "password": password},
        timeout=5.0,
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth_base_url() -> Iterator[str]:
    port = _find_free_port()
    base_url = f"http://{HOST}:{port}"
    process = _start_service(
        "services.auth_service.main:app",
        port,
        {
            "AUTH_SHARED_SECRET": AUTH_SHARED_SECRET,
            "AUTH_ISSUER": AUTH_ISSUER,
            "AUTH_AUDIENCE": AUTH_AUDIENCE,
        },
    )
    try:
        _wait_for_server(base_url=base_url, process=process)
        yield base_url
    finally:
        _stop_process(process)


@pytest.fixture(scope="session")
def notification_base_url() -> Iterator[str]:
    port = _find_free_port()
    base_url = f"http://{HOST}:{port}"
    process = _start_service(
        "services.notification_service.main:app",
        port,
        {"TEST_RESET_API_KEY": TEST_RESET_API_KEY},
    )
    try:
        _wait_for_server(base_url=base_url, process=process)
        yield base_url
    finally:
        _stop_process(process)


@pytest.fixture(scope="session")
def server_base_url(notification_base_url: str) -> Iterator[str]:
    port = _find_free_port()
    base_url = f"http://{HOST}:{port}"
    db_dir = ROOT / ".tmp"
    db_dir.mkdir(exist_ok=True)
    database_path = db_dir / "test-stack.db"
    if database_path.exists():
        database_path.unlink()

    process = _start_service(
        "app.main:app",
        port,
        {
            "DATABASE_URL": f"sqlite:///{database_path}",
            "AUTH_SHARED_SECRET": AUTH_SHARED_SECRET,
            "AUTH_ISSUER": AUTH_ISSUER,
            "AUTH_AUDIENCE": AUTH_AUDIENCE,
            "NOTIFICATION_SERVICE_URL": notification_base_url,
            "TEST_RESET_API_KEY": TEST_RESET_API_KEY,
        },
    )
    try:
        _wait_for_server(base_url=base_url, process=process)
        yield base_url
    finally:
        _stop_process(process)


@pytest.fixture
def reset_headers() -> dict[str, str]:
    return {"X-Test-Reset-Key": TEST_RESET_API_KEY}


@pytest.fixture
def auth_headers(auth_base_url: str) -> dict[str, str]:
    token = _fetch_token(auth_base_url, username="tester", password="tester-password")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_server_state(
    server_base_url: str,
    notification_base_url: str,
    reset_headers: dict[str, str],
) -> None:
    response = httpx.post(f"{server_base_url}/api/test/reset", headers=reset_headers, timeout=5.0)
    assert response.status_code == 200, response.text
    notifier_reset = httpx.post(
        f"{notification_base_url}/test/reset",
        headers=reset_headers,
        timeout=5.0,
    )
    assert notifier_reset.status_code == 200, notifier_reset.text


@pytest.fixture
def client(server_base_url: str) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=server_base_url, follow_redirects=True, timeout=5.0) as http_client:
        yield http_client
