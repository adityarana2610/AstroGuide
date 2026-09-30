"""Scenario and integration tests for FastAPI REST API endpoints.

Covers:
- Tier 1: Happy-path HTTP requests to all 5 calculation endpoints (/api/birth_chart, /api/numbers_stones, /api/find_dates, /api/daily_transits, /api/compatibility).
- Tier 2: Boundary, validation, and error-wrapping responses (422 Unprocessable Entity for schema violations, 200 success: False for calculation errors).
- Tier 3: Cross-feature pairwise workflows (feeding birth chart output directly into transit and numerology queries).
- Tier 4: Real-world consultation journey (full end-to-end multi-tool client sequence).
"""

import pytest


# ==============================================================================
# Tier 1: Core API Happy-Path Scenarios
# ==============================================================================

@pytest.mark.scenario
@pytest.mark.tier1
def test_api_birth_chart_success(client, valid_birth_chart_payload):
    """Tier 1: POST /api/birth_chart returns 200 OK with success=True and complete chart data."""
    resp = client.post("/api/birth_chart", json=valid_birth_chart_payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    assert "data" in data

    chart = data["data"]
    assert "ascendant" in chart
    assert "planets" in chart
    assert len(chart["planets"]) >= 9
    assert "houses" in chart
    assert len(chart["houses"]) == 12
    assert "svg_chart" in chart
    assert "<svg" in chart["svg_chart"]


@pytest.mark.scenario
@pytest.mark.tier1
def test_api_numbers_stones_success(client, valid_numbers_stones_payload):
    """Tier 1: POST /api/numbers_stones returns 200 OK with driver/conductor and gemstone."""
    resp = client.post("/api/numbers_stones", json=valid_numbers_stones_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    result = data["data"]
    assert result["driver_number"] == 6
    assert result["conductor_number"] == 4
    assert result["driver_planet"] == "Venus"
    assert "lucky_numbers" in result
    assert isinstance(result["lucky_numbers"], list)


@pytest.mark.scenario
@pytest.mark.tier1
def test_api_find_dates_success(client, valid_find_dates_payload):
    """Tier 1: POST /api/find_dates returns 200 OK with scored muhurtha dates."""
    resp = client.post("/api/find_dates", json=valid_find_dates_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    result = data["data"]
    assert "dates" in result
    assert len(result["dates"]) == 3
    for day in result["dates"]:
        assert "date" in day
        assert "score" in day
        assert "recommended_actions" in day


@pytest.mark.scenario
@pytest.mark.tier1
def test_api_daily_transits_success(client, valid_daily_transits_payload):
    """Tier 1: POST /api/daily_transits returns 200 OK with 9 Gochara planetary transits."""
    resp = client.post("/api/daily_transits", json=valid_daily_transits_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    result = data["data"]
    assert "transit_planets" in result
    assert len(result["transit_planets"]) == 9
    assert "overall_score" in result


@pytest.mark.scenario
@pytest.mark.tier1
def test_api_compatibility_success(client, valid_compatibility_payload):
    """Tier 1: POST /api/compatibility returns 200 OK with 36-point Ashtakoota score."""
    resp = client.post("/api/compatibility", json=valid_compatibility_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    result = data["data"]
    assert "total_points" in result
    assert result["max_points"] == 36.0
    assert "kootas" in result
    assert len(result["kootas"]) == 8


# ==============================================================================
# Tier 2: Boundary, Schema Validation & Error Wrapping
# ==============================================================================

@pytest.mark.scenario
@pytest.mark.tier2
def test_api_missing_required_fields_returns_422(client):
    """Tier 2: POST with missing required fields returns 422 Unprocessable Entity."""
    # Missing required 'birth_time', 'latitude', etc.
    resp = client.post("/api/birth_chart", json={"birth_date": "1990-05-15"})
    assert resp.status_code == 422


@pytest.mark.scenario
@pytest.mark.tier2
def test_api_pydantic_range_validation_returns_422(client):
    """Tier 2: Field values violating Pydantic boundaries (e.g., sign > 11) return 422."""
    # natal_moon_sign must be <= 11
    resp = client.post("/api/daily_transits", json={
        "natal_moon_sign": 15,
        "natal_moon_degree": 0.0,
        "target_date": "2026-10-01"
    })
    assert resp.status_code == 422


@pytest.mark.scenario
@pytest.mark.tier2
def test_api_calculation_error_wrapped_in_200(client):
    """Tier 2: Semantic calculation errors return HTTP 200 with success: False and error message."""
    resp = client.post("/api/numbers_stones", json={"birth_date": "invalid-date"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "error" in data


# ==============================================================================
# Tier 3: Cross-Feature Pairwise Workflow
# ==============================================================================

@pytest.mark.scenario
@pytest.mark.tier3
def test_pairwise_birth_chart_to_transits_workflow(client, valid_birth_chart_payload):
    """Tier 3: Generate birth chart, extract Moon sign, and query daily transits seamlessly."""
    # Step 1: Generate Birth Chart
    chart_resp = client.post("/api/birth_chart", json=valid_birth_chart_payload)
    assert chart_resp.status_code == 200
    chart_data = chart_resp.json()["data"]

    # Extract Moon's sign index from planetary positions
    moon_planet = next((p for p in chart_data["planets"] if p["name"] == "Moon"), None)
    assert moon_planet is not None, "Moon not found in birth chart planets"
    moon_sign_idx = moon_planet["sign_idx"]
    assert 0 <= moon_sign_idx <= 11

    # Step 2: Query Daily Transits for extracted Moon sign
    transit_resp = client.post("/api/daily_transits", json={
        "natal_moon_sign": moon_sign_idx,
        "natal_moon_degree": float(moon_planet["degree"]),
        "target_date": "2026-10-01"
    })
    assert transit_resp.status_code == 200
    transit_data = transit_resp.json()
    assert transit_data["success"] is True
    assert len(transit_data["data"]["transit_planets"]) == 9


# ==============================================================================
# Tier 4: Real-World Consultation Journey
# ==============================================================================

@pytest.mark.scenario
@pytest.mark.tier4
def test_real_world_marriage_consultation_journey(client):
    """Tier 4: Comprehensive user journey for wedding planning and relationship consultation.

    1. Calculate Bridegroom's numerology and gemstones.
    2. Calculate Bride's numerology and gemstones.
    3. Evaluate 36-point Guna Milan compatibility between their natal nakshatras.
    4. Search for auspicious wedding muhurtha dates over an autumn window.
    5. Evaluate planetary transits on the selected auspicious wedding date.
    """
    # 1. Bridegroom Numerology (Born 1991-03-24 -> Driver 6, Conductor 2)
    bg_num = client.post("/api/numbers_stones", json={"birth_date": "1991-03-24"})
    assert bg_num.status_code == 200
    assert bg_num.json()["success"] is True

    # 2. Bride Numerology (Born 1993-07-16 -> Driver 7, Conductor 9)
    br_num = client.post("/api/numbers_stones", json={"birth_date": "1993-07-16"})
    assert br_num.status_code == 200
    assert br_num.json()["success"] is True

    # 3. Compatibility: Rohini (3, Pada 1) vs Uttara Phalguni (11, Pada 2)
    compat = client.post("/api/compatibility", json={
        "person1_moon_nakshatra": 3,
        "person1_moon_pada": 1,
        "person2_moon_nakshatra": 11,
        "person2_moon_pada": 2
    })
    assert compat.status_code == 200
    compat_data = compat.json()
    assert compat_data["success"] is True
    assert 0.0 <= compat_data["data"]["total_points"] <= 36.0
    assert len(compat_data["data"]["kootas"]) == 8

    # 4. Search Muhurtha dates for wedding (Autumn 2026)
    dates_resp = client.post("/api/find_dates", json={
        "natal_moon_sign": 1,  # Taurus (Rohini)
        "natal_nakshatra": 3,
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5
    })
    assert dates_resp.status_code == 200
    dates_data = dates_resp.json()
    assert dates_data["success"] is True
    assert len(dates_data["data"]["dates"]) == 5

    # 5. Check transits on first evaluated wedding date
    selected_date = dates_data["data"]["dates"][0]["date"]
    transit_resp = client.post("/api/daily_transits", json={
        "natal_moon_sign": 1,
        "natal_moon_degree": 10.0,
        "target_date": selected_date
    })
    assert transit_resp.status_code == 200
    assert transit_resp.json()["success"] is True
