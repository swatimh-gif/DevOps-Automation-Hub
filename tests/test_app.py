import os
import json
import pytest
from app import create_app

@pytest.fixture
def client():
    """Create and configure a Flask test client."""
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_homepage_availability(client):
    """Test 1: Verify that the homepage loads with status code 200."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"DevOps Automation Hub" in response.data

def test_health_endpoint(client):
    """Test 2: Verify that the /health endpoint returns valid JSON with healthy status."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert data["service"] == "DevOps-Automation-Hub"
    assert "timestamp" in data
    assert "uptime_seconds" in data

def test_backend_api_metrics(client):
    """Test 3: Verify that the /api/metrics endpoint returns valid dashboard metrics."""
    response = client.get('/api/metrics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "total_runs" in data
    assert "success_rate" in data
    assert "latest_run" in data

def test_backend_api_status(client):
    """Test 4: Verify that the /api/status endpoint responds with system health."""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["system"] == "operational"
    assert "environment" in data
