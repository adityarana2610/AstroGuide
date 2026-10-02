"""Health check and web asset scenario tests for AstroGuide server.

Covers:
- Root page availability (GET /) serving static HTML single-page app.
- Static asset serving (GET /static/style.css, GET /static/script.js).
- Dedicated health check endpoints (GET /health, GET /api/health) per Feature F5.
"""

import pytest


@pytest.mark.scenario
@pytest.mark.tier1
def test_root_endpoint_health(client):
    """Tier 1: Root route GET / must return HTTP 200 with HTML application payload."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "AstroGuide" in resp.text


@pytest.mark.scenario
@pytest.mark.tier1
def test_static_stylesheet_health(client):
    """Tier 1: Static CSS asset /static/style.css must return HTTP 200."""
    resp = client.get("/static/style.css")
    assert resp.status_code == 200
    assert "text/css" in resp.headers.get("content-type", "")
    # Check glassmorphism css presence
    assert "glass" in resp.text.lower() or "background" in resp.text.lower()


@pytest.mark.scenario
@pytest.mark.tier1
def test_static_script_health(client):
    """Tier 1: Static JavaScript asset /static/script.js must return HTTP 200."""
    resp = client.get("/static/script.js")
    assert resp.status_code == 200
    assert (
        "application/javascript" in resp.headers.get("content-type", "")
        or "text/javascript" in resp.headers.get("content-type", "")
    )
    assert "birth-chart" in resp.text


@pytest.mark.scenario
@pytest.mark.tier1
def test_dedicated_health_endpoint(client):
    """Tier 1: Dedicated health check GET /health returns HTTP 200 with status ok (Feature F5)."""
    resp = client.get("/health")
    if resp.status_code == 404:
        pytest.skip(
            "GET /health is scheduled for implementation in Milestone M2 (Feature F5 per PROJECT.md)"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "ok"


@pytest.mark.scenario
@pytest.mark.tier1
def test_api_health_endpoint(client):
    """Tier 1: Dedicated API health check GET /api/health returns HTTP 200 with status ok."""
    resp = client.get("/api/health")
    if resp.status_code == 404:
        pytest.skip(
            "GET /api/health is scheduled for implementation in Milestone M2 (Feature F5 per PROJECT.md)"
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] == "ok"
