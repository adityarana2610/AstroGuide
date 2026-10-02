"""Unit tests for core AstroGuide astrology calculation tools.

Verifies:
- birth_chart: Swiss Ephemeris calculations, Whole-Sign houses, SVG chart generators (North & South Indian).
- numbers_stones: Numerological Driver/Conductor reduction, gemstone & lucky number deduplication.
- daily_transits: Gochara transit scoring, house calculations, Vedha obstruction rules.
- compatibility: Ashtakoota 36-point Guna Milan matching, 8 individual kootas, Yoni scoring.
- find_dates: Multi-day muhurtha scoring, Tithi, Chandrabala, Tarabala, Rahu Kalam.
"""

import pytest
from astroguide.tools.birth_chart import get_birth_chart
from astroguide.tools.numbers_stones import get_numbers_and_stones
from astroguide.tools.daily_transits import get_daily_transits
from astroguide.tools.compatibility import match_compatibility
from astroguide.tools.find_dates import find_dates


# ==============================================================================
# 1. Birth Chart Tool Unit Tests
# ==============================================================================

@pytest.mark.unit
@pytest.mark.tier1
def test_birth_chart_happy_path(valid_birth_chart_payload):
    """Tier 1: Verify get_birth_chart produces 9 planets, 12 houses, ascendant, and SVG."""
    res = get_birth_chart.invoke(valid_birth_chart_payload)
    assert isinstance(res, dict)
    assert "error" not in res, f"Unexpected error in birth chart: {res.get('error')}"

    # Ascendant validation
    assert "ascendant" in res
    asc = res["ascendant"]
    assert "sign" in asc
    assert "degree" in asc
    assert 0 <= asc["sign_idx"] <= 11
    assert 0.0 <= asc["degree"] <= 30.0

    # Planets validation (must have at least 9 classical Vedic planets)
    assert "planets" in res
    planets = res["planets"]
    planet_names = [p["name"] for p in planets]
    expected_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for ep in expected_planets:
        assert ep in planet_names, f"Planet {ep} missing from birth chart calculation"

    # Houses validation (exactly 12 whole sign houses)
    assert "houses" in res
    assert len(res["houses"]) == 12

    # SVG chart validation
    assert "svg_chart" in res
    assert res["svg_chart"].startswith("<svg")
    assert res["svg_chart"].endswith("</svg>")


@pytest.mark.unit
@pytest.mark.tier1
def test_birth_chart_north_and_south_styles(valid_birth_chart_payload):
    """Tier 1: Verify both North and South Indian chart styles generate distinct valid SVG."""
    # North Indian
    payload_north = dict(valid_birth_chart_payload, chart_style="north")
    res_north = get_birth_chart.invoke(payload_north)
    assert "<svg" in res_north["svg_chart"]
    assert "</svg>" in res_north["svg_chart"]
    # North Indian uses diagonal and crossing lines
    assert 'x1="0" y1="0" x2="400" y2="400"' in res_north["svg_chart"]

    # South Indian
    payload_south = dict(valid_birth_chart_payload, chart_style="south")
    res_south = get_birth_chart.invoke(payload_south)
    assert "<svg" in res_south["svg_chart"]
    assert "</svg>" in res_south["svg_chart"]
    # South Indian uses inner rectangle grid geometry
    assert 'x="100" y="100" width="200" height="200"' in res_south["svg_chart"]


@pytest.mark.unit
@pytest.mark.tier2
def test_birth_chart_invalid_date_error_handling(valid_birth_chart_payload):
    """Tier 2: Invalid date format must return graceful error dict without crashing."""
    payload = dict(valid_birth_chart_payload, birth_date="not-a-date")
    res = get_birth_chart.invoke(payload)
    assert isinstance(res, dict)
    assert "error" in res


# ==============================================================================
# 2. Numbers & Stones Tool Unit Tests
# ==============================================================================

@pytest.mark.unit
@pytest.mark.tier1
def test_numbers_stones_driver_conductor_math():
    """Tier 1: Verify driver and conductor single-digit reduction math."""
    # Date: 1995-10-15
    # Driver = 1 + 5 = 6 (Venus)
    # Conductor = 1+9+9+5 + 1+0 + 1+5 = 24 + 1 + 6 = 31 -> 3 + 1 = 4 (Rahu)
    res = get_numbers_and_stones.invoke({"birth_date": "1995-10-15"})
    assert "error" not in res
    assert res["driver_number"] == 6
    assert res["conductor_number"] == 4
    assert res["driver_planet"] == "Venus"
    assert res["conductor_planet"] == "Rahu"
    assert "lucky_numbers" in res
    assert 6 in res["lucky_numbers"]
    assert 4 in res["lucky_numbers"]
    # Check deduplication
    assert len(res["lucky_numbers"]) == len(set(res["lucky_numbers"]))


@pytest.mark.unit
@pytest.mark.tier1
def test_numbers_stones_single_digit_day():
    """Tier 1: Verify single digit birthday calculation."""
    # Date: 2000-01-05 -> Day 5 -> Driver 5 (Mercury)
    # Conductor: 2+0+0+0 + 0+1 + 0+5 = 8 (Saturn)
    res = get_numbers_and_stones.invoke({"birth_date": "2000-01-05"})
    assert "error" not in res
    assert res["driver_number"] == 5
    assert res["conductor_number"] == 8
    assert res["driver_planet"] == "Mercury"
    assert res["conductor_planet"] == "Saturn"


@pytest.mark.unit
@pytest.mark.tier2
def test_numbers_stones_invalid_date():
    """Tier 2: Non-existent calendar date returns error dict."""
    res = get_numbers_and_stones.invoke({"birth_date": "2026-02-30"})
    assert isinstance(res, dict)
    assert "error" in res


# ==============================================================================
# 3. Daily Transits Tool Unit Tests
# ==============================================================================

@pytest.mark.unit
@pytest.mark.tier1
def test_daily_transits_happy_path(valid_daily_transits_payload):
    """Tier 1: Verify get_daily_transits computes Gochara transit positions and scores."""
    res = get_daily_transits.invoke(valid_daily_transits_payload)
    assert isinstance(res, dict)
    assert "error" not in res

    assert "target_date" in res
    assert "transit_planets" in res
    assert len(res["transit_planets"]) == 9

    planet = res["transit_planets"][0]
    assert "name" in planet
    assert "transit_house" in planet
    assert "is_favourable" in planet
    assert "is_blocked_by_vedha" in planet

    assert "favourable_count" in res
    assert "unfavourable_count" in res
    assert "overall_score" in res


@pytest.mark.unit
@pytest.mark.tier2
def test_daily_transits_out_of_bounds_moon_sign():
    """Tier 2: Out of bounds moon sign index returns error dict."""
    res_high = get_daily_transits.invoke({
        "natal_moon_sign": 12,
        "natal_moon_degree": 0.0,
        "target_date": "2026-10-01"
    })
    assert "error" in res_high

    res_neg = get_daily_transits.invoke({
        "natal_moon_sign": -1,
        "natal_moon_degree": 0.0,
        "target_date": "2026-10-01"
    })
    assert "error" in res_neg


# ==============================================================================
# 4. Compatibility (Ashtakoota) Tool Unit Tests
# ==============================================================================

@pytest.mark.unit
@pytest.mark.tier1
def test_compatibility_ashtakoota_all_kootas(valid_compatibility_payload):
    """Tier 1: Verify all 8 Kootas are calculated and sum to total_points."""
    res = match_compatibility.invoke(valid_compatibility_payload)
    assert isinstance(res, dict)
    assert "error" not in res

    assert "total_points" in res
    assert "max_points" in res
    assert res["max_points"] == 36.0
    assert 0.0 <= res["total_points"] <= 36.0
    assert "kootas" in res
    assert len(res["kootas"]) == 8

    expected_kootas = {
        "Varna": 1.0,
        "Vashya": 2.0,
        "Tara": 3.0,
        "Yoni": 4.0,
        "Graha Maitri": 5.0,
        "Gana": 6.0,
        "Bhakoot": 7.0,
        "Nadi": 8.0
    }

    sum_obtained = 0.0
    for koota in res["kootas"]:
        name = koota["name"]
        assert name in expected_kootas, f"Unexpected koota: {name}"
        assert koota["max"] == expected_kootas[name]
        assert 0.0 <= koota["obtained"] <= koota["max"]
        sum_obtained += koota["obtained"]

    assert abs(res["total_points"] - sum_obtained) < 0.01


@pytest.mark.unit
@pytest.mark.tier2
def test_compatibility_out_of_bounds_inputs():
    """Tier 2: Out of bounds nakshatra or pada returns error dict."""
    res = match_compatibility.invoke({
        "person1_moon_nakshatra": 99,
        "person1_moon_pada": 1,
        "person2_moon_nakshatra": 0,
        "person2_moon_pada": 1
    })
    assert "error" in res


# ==============================================================================
# 5. Find Dates (Muhurtha) Tool Unit Tests
# ==============================================================================

@pytest.mark.unit
@pytest.mark.tier1
def test_find_dates_multi_day_evaluation(valid_find_dates_payload):
    """Tier 1: Verify find_dates evaluates each day in date range with Muhurtha scores."""
    res = find_dates.invoke(valid_find_dates_payload)
    assert isinstance(res, dict)
    assert "error" not in res

    assert "dates" in res
    dates = res["dates"]
    assert len(dates) == 3, f"Expected 3 evaluated days, got {len(dates)}"

    first_day = dates[0]
    assert "date" in first_day
    assert "score" in first_day
    assert "tithi" in first_day
    assert "moon_sign" in first_day
    assert "recommended_actions" in first_day


@pytest.mark.unit
@pytest.mark.tier2
def test_find_dates_inverted_range_error():
    """Tier 2: end_date preceding start_date returns error dict."""
    res = find_dates.invoke({
        "natal_moon_sign": 0,
        "natal_nakshatra": 0,
        "start_date": "2026-10-10",
        "end_date": "2026-10-01",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5
    })
    assert "error" in res
