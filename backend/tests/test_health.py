"""
Test Giai đoạn 1 — Health Check Endpoint
-----------------------------------------
Chạy: pytest backend/tests/test_health.py -v
(chạy từ thư mục gốc repo: d:\\Sentrix)
"""

from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_health_returns_200():
    """GET /health phải trả về HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}"
    )


def test_health_returns_correct_json():
    """GET /health phải trả về JSON đúng cấu trúc."""
    response = client.get("/health")
    data = response.json()

    assert data["status"] == "ok", f"Expected status='ok', got {data['status']}"
    assert "version" in data, "Thiếu field 'version'"
    assert "message" in data, "Thiếu field 'message'"


def test_health_content_type():
    """GET /health phải trả về Content-Type: application/json."""
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
