"""Playwright e2e test fixtures.

Starts the real FastAPI server with NEXTFERRY_TEST_MODE set so
wsdot_client.py returns fixture data instead of calling the WSDOT API.
"""

import os
import socket
import subprocess
import sys
import time

import pytest
import requests


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 15.0) -> None:
    """Poll until the server responds or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = requests.get(url, timeout=2)
            if resp.ok:
                return
        except requests.ConnectionError:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"Server at {url} did not start within {timeout}s")


@pytest.fixture(scope="session")
def server_port():
    return _find_free_port()


@pytest.fixture(scope="session")
def server_url(server_port):
    return f"http://127.0.0.1:{server_port}"


@pytest.fixture(scope="session")
def _server_process(server_port, server_url):
    """Start uvicorn with test mode enabled (session-scoped, one server for all tests)."""
    env = {
        **os.environ,
        "NEXTFERRY_TEST_MODE": "two_boats_at_dock",
        # Suppress WSDOT_API_KEY requirement in test mode
        "WSDOT_API_KEY": "",
    }
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(server_port),
            "--log-level",
            "warning",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_for_server(server_url)
        yield proc
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.fixture()
def live_server(_server_process, server_url):
    """Provide the server URL to tests (ensures server is running)."""
    return server_url


@pytest.fixture()
def page(browser, live_server):
    """Create a new page pointed at the live test server."""
    p = browser.new_page()
    p.goto(live_server)
    yield p
    p.close()
