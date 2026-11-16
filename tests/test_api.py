import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client

def test_all_pages_render_successfully(client):
    """Verifies that all 8 primary application views render with HTTP 200 OK."""
    endpoints = [
        '/',
        '/pipeline',
        '/history',
        '/testing',
        '/docker',
        '/deployment',
        '/monitoring',
        '/logs'
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200, f"Endpoint {endpoint} failed with status {response.status_code}"

def test_api_endpoints(client):
    """Verifies that JSON API endpoints respond with valid structures."""
    # Health endpoint
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json['status'] == 'healthy'

    # Metrics endpoint
    res = client.get('/api/metrics')
    assert res.status_code == 200
    assert 'total_runs' in res.json

    # Monitoring endpoint
    res = client.get('/api/monitoring/metrics')
    assert res.status_code == 200
    assert 'cpu_percent' in res.json

    # Docker status endpoint
    res = client.get('/api/docker/status')
    assert res.status_code == 200
    assert 'available' in res.json

def test_github_webhook_endpoint(client, monkeypatch):
    """Verifies that the GitHub Webhook receiver accepts payload and triggers pipeline."""
    # Mock execute_pipeline to verify route processing without nested subshell
    import app as app_module
    monkeypatch.setattr(app_module, "execute_pipeline", lambda trigger_type, simulate_failure: {
        "run_id": "RUN-TEST",
        "status": "SUCCESS",
        "duration": 1.2
    })

    payload = {
        "head_commit": {
            "id": "a1b2c3d4e5f6",
            "message": "feat: update healthcheck monitoring logic"
        },
        "sender": {
            "login": "devops-engineer"
        }
    }
    response = client.post(
        '/api/webhook/github',
        json=payload,
        headers={"X-GitHub-Event": "push"}
    )
    assert response.status_code == 202
    data = response.json
    assert "result" in data
    assert data["result"]["status"] == "SUCCESS"
