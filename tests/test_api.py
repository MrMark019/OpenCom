"""
Tests for FastAPI backend
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data


def test_list_ports():
    """Test ports listing endpoint"""
    response = client.get("/api/ports")
    assert response.status_code in [200, 500]  # 500 if no serial ports available


def test_get_status():
    """Test status endpoint"""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert "connected" in data
    assert "send_count" in data
    assert "receive_count" in data


def test_counters():
    """Test counters endpoint"""
    response = client.get("/api/counters")
    assert response.status_code == 200
    data = response.json()
    assert "send_count" in data
    assert "receive_count" in data


def test_reset_counters():
    """Test reset counters endpoint"""
    response = client.post("/api/counters/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
