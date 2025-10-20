# tests/test_main.py

import pytest
from fastapi.testclient import TestClient

from app.main import app  # adjust path if needed
from app.utils.settings import settings

client = TestClient(app)

TEST_ROOT_GET = {
        "message": "Welcome to" + settings.app_title + "!",
        "version": settings.app_version
    }

def test_root_endpoint():
    """GET / should return metadata and API info."""

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == TEST_ROOT_GET, f"Root endpoint message unexpected output: {response.json()}"


def test_health_endpoint():
    """GET /health should confirm the service is alive."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "databy-ai"}