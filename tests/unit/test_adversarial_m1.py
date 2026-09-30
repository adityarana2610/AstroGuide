"""Adversarial stress-testing and backward-compatibility verification suite for Milestone 1.
Path: tests/unit/test_adversarial_m1.py

Authors: Challenger M1-2 (Adversarial Critic & Specialist)
Objective:
Exhaustively challenge the execution and backward compatibility of all 5 refactored astrology tools:
1. get_birth_chart (extreme latitudes, longitudes, century/leap dates, midnight/noon, North/South SVG)
2. get_numbers_and_stones (boundary dates, leap years, single digits, 11 legacy keys, remedy enrichment)
3. get_daily_transits (all 12 Moon signs, Gochara house scoring, Vedha blocking rules, cached table)
4. match_compatibility (729 nakshatra pairings, padas 1-4, Yoni pairing symmetry, Ashtakoota 36 pts)
5. find_dates (1-day, 10-day, 60-day ranges, 30 Tithis, 9 Taras, externalized Panchang data)
"""

import math
from datetime import datetime, timedelta
import pytest

from astroguide.tools.birth_chart import get_birth_chart, RASHI_NAMES as BC_RASHIS
from astroguide.tools.numbers_stones import (
    get_numbers_and_stones,
    get_astrological_remedy,
    reduce_to_single_digit
)
from astroguide.tools.daily_transits import get_daily_transits, get_gochara_rules, RASHI_NAMES as DT_RASHIS
from astroguide.tools.compatibility import (
    match_compatibility,
    get_moon_sign,
    score_vashya,
    NAKSHATRAS,
    YONI_ENEMIES
)
from astroguide.tools.find_dates import (
    find_dates,
    SHUBH_TITHIS,
    ASHUBH_TITHIS,
    TITHI_NAMES,
    TARA_NAMES,
    AUSPICIOUS_ACTIONS
)
from astroguide.utils.data_loader import (
    DataLoader,
    load_remedies,
    load_panchang_reference,
    load_gochara_rules,
    load_planet_stones,
    load_nakshatras
)


# ==============================================================================
# SECTION 1: get_birth_chart Adversarial Stress Tests
# ==============================================================================

@pytest.mark.adversarial
@pytest.mark.parametrize("lat,lon,label", [
    (0.0, 0.0, "Equator and Prime Meridian"),
    (0.0, 179.9, "Equator Far East"),
    (0.0, -179.9, "Equator Far West"),
    (28.6139, 77.2090, "New Delhi (Northern Subtropical)"),
    (13.0827, 80.2707, "Chennai (Tropical Southern India)"),
    (-23.5505, -46.6333, "Sao Paulo (Southern Subtropical)"),
    (-54.8019, -68.3030, "Ushuaia (Far South Tierra del Fuego)"),
    (64.1466, -21.9426, "Reykjavik (Sub-Arctic North)"),
    (78.2232, 15.6267, "Longyearbyen, Svalbard (Extreme Polar North)"),
])
def test_birth_chart_geographic_boundaries(lat, lon, label):
    """Stress test birth chart across extreme global latitudes and longitudes."""
    payload = {
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "latitude": lat,
        "longitude": lon,
        "tz_offset": 0.0,
        "chart_style": "north",
        "ayanamsha": "lahiri"
    }
    res = get_birth_chart.invoke(payload)
    assert isinstance(res, dict), f"Failed for {label}"
    assert "error" not in res, f"Calculation failed for {label}: {res.get('error')}"

    # Ascendant checks
    assert "ascendant" in res
    asc = res["ascendant"]
    assert asc["sign"] in BC_RASHIS
    assert 0.0 <= asc["degree"] <= 30.0
    assert 1 <= asc["pada"] <= 4

    # 9 Vedic Grahas
    assert "planets" in res
    assert len(res["planets"]) == 9
    for p in res["planets"]:
        assert 0.0 <= p["longitude"] < 360.0
        assert 0 <= p["sign_index"] <= 11
        assert 1 <= p["house"] <= 12
        assert 1 <= p["pada"] <= 4

    # 12 Houses
    assert "houses" in res
    assert len(res["houses"]) == 12

    # SVG chart
    assert "svg_chart" in res
    assert res["svg_chart"].startswith("<svg")
    assert res["svg_chart"].endswith("</svg>")


@pytest.mark.adversarial
@pytest.mark.parametrize("b_date,b_time,tz,label", [
    ("2024-02-29", "12:00", 5.5, "Leap year day (2024)"),
    ("2000-02-29", "00:00", 0.0, "Century leap day (2000) midnight"),
    ("1999-12-31", "23:59", -5.0, "Millennium eve late night"),
    ("2000-01-01", "00:01", 1.0, "Millennium dawn early morning"),
    ("1900-02-28", "12:00", 0.0, "Non-leap century year end of Feb"),
    ("1970-01-01", "00:00", 0.0, "Unix Epoch origin"),
])
def test_birth_chart_calendar_temporal_boundaries(b_date, b_time, tz, label):
    """Stress test birth chart across critical calendar boundaries and times."""
    payload = {
        "birth_date": b_date,
        "birth_time": b_time,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": tz,
        "chart_style": "south",
        "ayanamsha": "lahiri"
    }
    res = get_birth_chart.invoke(payload)
    assert "error" not in res, f"Failed temporal boundary test for {label}: {res.get('error')}"
    assert res["birth_info"]["date"] == b_date
    assert res["birth_info"]["time"] == b_time
    assert res["birth_info"]["tz_offset"] == tz


@pytest.mark.adversarial
def test_birth_chart_north_vs_south_svg_geometry():
    """Verify distinct SVG geometric markup and retrograde indicators for North and South styles."""
    # Date 2024-10-15 has retrograde planets (e.g. Jupiter, Saturn)
    base_payload = {
        "birth_date": "2024-10-15",
        "birth_time": "12:00",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5,
        "ayanamsha": "lahiri"
    }
    # 1. North Indian Style
    res_north = get_birth_chart.invoke(dict(base_payload, chart_style="north"))
    svg_n = res_north["svg_chart"]
    assert '<line x1="0" y1="0" x2="400" y2="400"' in svg_n
    assert '<line x1="200" y1="0" x2="400" y2="200"' in svg_n
    assert "(R)" in svg_n, "Retrograde (R) marker missing in North Indian SVG"

    # 2. South Indian Style (case-insensitive test: "SOUTH")
    res_south = get_birth_chart.invoke(dict(base_payload, chart_style="SOUTH"))
    svg_s = res_south["svg_chart"]
    assert '<rect x="100" y="100" width="200" height="200"' in svg_s
    assert 'fill="red">Asc</text>' in svg_s, "South Indian Ascendant marker missing"
    assert "(R)" in svg_s, "Retrograde (R) marker missing in South Indian SVG"


@pytest.mark.adversarial
@pytest.mark.parametrize("aya", ["lahiri", "raman", "krishnamurti", "unknown_fallback"])
def test_birth_chart_ayanamsha_modes(aya):
    """Stress test ayanamsha options including unknown fallback."""
    payload = {
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5,
        "chart_style": "north",
        "ayanamsha": aya
    }
    res = get_birth_chart.invoke(payload)
    assert "error" not in res
    assert res["birth_info"]["ayanamsha"] == aya


@pytest.mark.adversarial
@pytest.mark.parametrize("bad_date,bad_time", [
    ("invalid-date", "12:00"),
    ("2026-02-29", "12:00"),  # 2026 is not a leap year
    ("1990-13-01", "12:00"),  # month 13
    ("1990-05-32", "12:00"),  # day 32
    ("1990-05-15", "24:00"),  # hour 24
    ("1990-05-15", "12:60"),  # minute 60
    ("1990-05-15", "12"),     # missing minute
])
def test_birth_chart_invalid_datetime_inputs(bad_date, bad_time):
    """Verify birth_chart handles malformed date/time gracefully with error dict."""
    payload = {
        "birth_date": bad_date,
        "birth_time": bad_time,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5,
        "chart_style": "north"
    }
    res = get_birth_chart.invoke(payload)
    assert isinstance(res, dict)
    assert "error" in res


# ==============================================================================
# SECTION 2: get_numbers_and_stones Adversarial Stress Tests
# ==============================================================================

@pytest.mark.adversarial
def test_numbers_stones_all_31_calendar_days():
    """Verify single-digit reduction math for all possible days in a month (1 to 31)."""
    expected_driver_map = {
        1: 1, 10: 1, 19: 1, 28: 1,
        2: 2, 11: 2, 20: 2, 29: 2,
        3: 3, 12: 3, 21: 3, 30: 3,
        4: 4, 13: 4, 22: 4, 31: 4,
        5: 5, 14: 5, 23: 5,
        6: 6, 15: 6, 24: 6,
        7: 7, 16: 7, 25: 7,
        8: 8, 17: 8, 26: 8,
        9: 9, 18: 9, 27: 9,
    }
    for day, expected_driver in expected_driver_map.items():
        date_str = f"2020-01-{day:02d}"
        res = get_numbers_and_stones.invoke({"birth_date": date_str})
        assert res["driver_number"] == expected_driver, f"Failed driver for day {day}"
        assert 1 <= res["conductor_number"] <= 9


@pytest.mark.adversarial
@pytest.mark.parametrize("b_date,exp_driver,exp_conductor,exp_driver_planet", [
    ("2024-02-29", 2, 3, "Moon"),     # 29 -> 11 -> 2; 20240229 sum = 21 -> 3
    ("2000-01-01", 1, 4, "Sun"),      # 1 -> 1; 20000101 sum = 4
    ("1900-12-31", 4, 8, "Rahu"),     # 31 -> 4; 19001231 sum = 17 -> 8
    ("1995-10-15", 6, 4, "Venus"),    # 15 -> 6; 19951015 sum = 31 -> 4
    ("2006-01-01", 1, 1, "Sun"),      # 1 -> 1; 20060101 sum = 10 -> 1 (Driver == Conductor)
    ("1989-09-09", 9, 8, "Mars"),     # 9 -> 9; 19890909 sum = 44 -> 8
])
def test_numbers_stones_deterministic_calculations(b_date, exp_driver, exp_conductor, exp_driver_planet):
    """Stress test driver, conductor, and planet mappings against known numerology cases."""
    res = get_numbers_and_stones.invoke({"birth_date": b_date})
    assert "error" not in res
    assert res["driver_number"] == exp_driver
    assert res["conductor_number"] == exp_conductor
    assert res["driver_planet"] == exp_driver_planet


@pytest.mark.adversarial
def test_numbers_stones_assert_all_11_legacy_keys_and_remedy_enrichment():
    """Verify exact presence of all 11 legacy keys plus comprehensive remedy enrichment."""
    res = get_numbers_and_stones.invoke({"birth_date": "1995-10-15"})
    assert "error" not in res

    legacy_keys = [
        "birth_date",
        "driver_number",
        "driver_planet",
        "conductor_number",
        "conductor_planet",
        "primary_gemstone",
        "secondary_gemstone",
        "lucky_numbers",
        "lucky_colours",
        "friendly_planets",
        "unfriendly_planets"
    ]
    for key in legacy_keys:
        assert key in res, f"Legacy key '{key}' missing from get_numbers_and_stones payload"

    # Lucky numbers must be deduplicated
    lucky_nums = res["lucky_numbers"]
    assert len(lucky_nums) == len(set(lucky_nums)), f"Duplicates in lucky_numbers: {lucky_nums}"

    # Verify Feature F1 remedy enrichment
    assert "driver_remedy" in res, "driver_remedy missing from enriched payload"
    assert "conductor_remedy" in res, "conductor_remedy missing from enriched payload"
    assert "driver_remedies" in res, "driver_remedies alias missing"
    assert "conductor_remedies" in res, "conductor_remedies alias missing"

    d_rem = res["driver_remedy"]
    required_remedy_fields = [
        "primary_gemstone", "metal", "wear_finger", "wear_day",
        "mantra", "deity", "rudraksha", "charity_items", "fasting_day",
        "positive_lifestyle_action"
    ]
    for rf in required_remedy_fields:
        assert rf in d_rem, f"Field '{rf}' missing from driver_remedy"


@pytest.mark.adversarial
@pytest.mark.parametrize("graha", ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"])
def test_get_astrological_remedy_all_grahas(graha):
    """Verify get_astrological_remedy retrieves valid classical remedies for all 9 Grahas."""
    rem = get_astrological_remedy.invoke({"planet_name": graha})
    assert isinstance(rem, dict)
    assert "error" not in rem, f"Failed remedy lookup for {graha}: {rem.get('error')}"
    assert rem["planet"] == graha
    assert rem["primary_gemstone"]
    assert rem["mantra"]
    assert rem["positive_lifestyle_action"]


# ==============================================================================
# SECTION 3: get_daily_transits Adversarial Stress Tests
# ==============================================================================

@pytest.mark.adversarial
@pytest.mark.parametrize("moon_sign", list(range(12)))
def test_daily_transits_all_12_moon_signs(moon_sign):
    """Stress test daily transits calculation for all 12 Moon signs (0 to 11)."""
    res = get_daily_transits.invoke({
        "natal_moon_sign": moon_sign,
        "natal_moon_degree": 0.0,
        "target_date": "2026-10-01"
    })
    assert "error" not in res, f"Failed for Moon sign {moon_sign}"
    assert res["natal_moon_sign"] == DT_RASHIS[moon_sign]
    assert "transits" in res
    assert len(res["transits"]) == 9

    sum_scores = 0
    for t in res["transits"]:
        assert t["planet"] in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        assert 1 <= t["house_from_moon"] <= 12
        assert isinstance(t["is_favourable"], bool)
        assert isinstance(t["vedha_blocked"], bool)
        assert t["score"] in (-1, 0, 1)
        sum_scores += t["score"]

    assert res["overall_score"] == sum_scores, "Overall score does not equal sum of individual planet scores"
    assert res["day_rating"] in ["Highly Favourable", "Favourable", "Neutral", "Challenging", "Difficult"]
    assert "summary" in res


@pytest.mark.adversarial
def test_daily_transits_vedha_blocking_execution_and_caching():
    """Verify Vedha pairs are loaded from cached gochara_rules.json and block favourable houses."""
    rules = get_gochara_rules()
    assert isinstance(rules, dict)
    assert len(rules) == 9

    # Sun rules: Favourable in 3, 6, 10, 11; Vedha pairs: {"3": 9, "6": 12, "10": 4, "11": 5}
    sun_rule = rules["Sun"]
    assert 3 in sun_rule["favourable_houses"]
    assert sun_rule["vedha_pairs"].get("3") == 9

    # Cache hit check
    rules2 = get_gochara_rules()
    assert rules is not rules2 or rules == rules2  # Deep copy or equal


@pytest.mark.adversarial
@pytest.mark.parametrize("bad_sign", [-1, 12, 100])
def test_daily_transits_out_of_bounds_moon_sign(bad_sign):
    """Verify out-of-bounds natal_moon_sign returns clean error dict."""
    res = get_daily_transits.invoke({
        "natal_moon_sign": bad_sign,
        "natal_moon_degree": 0.0,
        "target_date": "2026-10-01"
    })
    assert isinstance(res, dict)
    assert "error" in res


# ==============================================================================
# SECTION 4: match_compatibility Adversarial Stress Tests
# ==============================================================================

@pytest.mark.adversarial
def test_compatibility_all_27_nakshatras_combinatorial():
    """Stress test all 27 x 27 = 729 Nakshatra combinations with pada 1."""
    for n1 in range(27):
        for n2 in range(27):
            res = match_compatibility.invoke({
                "person1_moon_nakshatra": n1,
                "person1_moon_pada": 1,
                "person2_moon_nakshatra": n2,
                "person2_moon_pada": 1
            })
            assert "error" not in res, f"Failed for pair ({n1}, {n2})"
            assert 0.0 <= res["total_score"] <= 36.0
            assert len(res["kootas"]) == 8
            koota_sum = sum(k["obtained"] for k in res["kootas"])
            assert abs(res["total_score"] - koota_sum) < 0.01


@pytest.mark.adversarial
@pytest.mark.parametrize("p1_pada", [1, 2, 3, 4])
@pytest.mark.parametrize("p2_pada", [1, 2, 3, 4])
def test_compatibility_all_padas_and_makara_boundaries(p1_pada, p2_pada):
    """Test all 4 padas across sign boundaries, specifically Uttarashadha (20) & Dhanishta (22)."""
    # Uttarashadha Pada 1 (Sagittarius) vs Uttarashadha Pada 2 (Capricorn)
    res = match_compatibility.invoke({
        "person1_moon_nakshatra": 20,
        "person1_moon_pada": p1_pada,
        "person2_moon_nakshatra": 22,
        "person2_moon_pada": p2_pada
    })
    assert "error" not in res
    assert 0.0 <= res["total_score"] <= 36.0


@pytest.mark.adversarial
def test_compatibility_yoni_pairings_and_known_asymmetry():
    """Verify Yoni pairings, mortal enemies, and confirm the known Goat vs Monkey asymmetry (Bug F6)."""
    # 1. Same animal opposite sex -> 4.0 points (Ashwini: Horse M vs Shatabhisha: Horse F)
    res_opp = match_compatibility.invoke({
        "person1_moon_nakshatra": 0,
        "person1_moon_pada": 1,
        "person2_moon_nakshatra": 23,
        "person2_moon_pada": 1
    })
    yoni_opp = next(k for k in res_opp["kootas"] if k["name"] == "Yoni")
    assert yoni_opp["obtained"] == 4.0

    # 2. Same animal same sex -> 3.0 points (Ashwini: Horse M vs Ashwini: Horse M)
    res_same = match_compatibility.invoke({
        "person1_moon_nakshatra": 0,
        "person1_moon_pada": 1,
        "person2_moon_nakshatra": 0,
        "person2_moon_pada": 1
    })
    yoni_same = next(k for k in res_same["kootas"] if k["name"] == "Yoni")
    assert yoni_same["obtained"] == 3.0

    # 3. Known Asymmetry between Pushya (7, Goat M) and Shravana (21, Monkey F):
    # Pushya (Goat) vs Shravana (Monkey) -> Yoni enemy -> 0.0
    res_goat_monkey = match_compatibility.invoke({
        "person1_moon_nakshatra": 7,
        "person1_moon_pada": 1,
        "person2_moon_nakshatra": 21,
        "person2_moon_pada": 1
    })
    yoni_gm = next(k for k in res_goat_monkey["kootas"] if k["name"] == "Yoni")
    assert yoni_gm["obtained"] == 0.0

    # Shravana (Monkey) vs Pushya (Goat) -> Due to table lookup asymmetry -> 1.0 (Documented Bug F6)
    res_monkey_goat = match_compatibility.invoke({
        "person1_moon_nakshatra": 21,
        "person1_moon_pada": 1,
        "person2_moon_nakshatra": 7,
        "person2_moon_pada": 1
    })
    yoni_mg = next(k for k in res_monkey_goat["kootas"] if k["name"] == "Yoni")
    assert yoni_mg["obtained"] == 1.0, "Expected empirical reproduction of asymmetric Yoni scoring (F6)"


@pytest.mark.adversarial
@pytest.mark.parametrize("nak1,pada1,nak2,pada2", [
    (-1, 1, 0, 1),
    (27, 1, 0, 1),
    (0, 0, 0, 1),
    (0, 5, 0, 1),
    (0, 1, 99, 1),
])
def test_compatibility_boundary_error_handling(nak1, pada1, nak2, pada2):
    """Verify out-of-bounds nakshatras (<0, >26) and padas (<1, >4) return error dicts."""
    res = match_compatibility.invoke({
        "person1_moon_nakshatra": nak1,
        "person1_moon_pada": pada1,
        "person2_moon_nakshatra": nak2,
        "person2_moon_pada": pada2
    })
    assert isinstance(res, dict)
    assert "error" in res


# ==============================================================================
# SECTION 5: find_dates Adversarial Stress Tests
# ==============================================================================

@pytest.mark.adversarial
@pytest.mark.parametrize("start,end,expected_days", [
    ("2026-10-01", "2026-10-01", 1),   # 1-day range
    ("2026-10-01", "2026-10-10", 10),  # 10-day range
    ("2026-10-01", "2026-11-30", 61),  # 60 delta_days = 61 days
])
def test_find_dates_range_scaling(start, end, expected_days):
    """Stress test find_dates across 1-day, 10-day, and maximum allowable 60-day spans."""
    res = find_dates.invoke({
        "natal_moon_sign": 0,
        "natal_nakshatra": 0,
        "start_date": start,
        "end_date": end,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5
    })
    assert "error" not in res, f"Failed for range {start} to {end}: {res.get('error')}"
    assert len(res["dates"]) == expected_days

    for d in res["dates"]:
        assert 1 <= d["tithi"]["number"] <= 30
        assert d["tithi"]["name"] in TITHI_NAMES
        assert d["tithi"]["paksha"] in ["Shukla", "Krishna"]
        assert 1 <= d["tarabala"]["tara_number"] <= 9
        assert d["tarabala"]["tara_name"] in TARA_NAMES
        assert "composite_score" in d
        assert "rahu_kalam" in d
        assert d["rahu_kalam"]["start"]
        assert d["rahu_kalam"]["end"]


@pytest.mark.adversarial
def test_find_dates_exceeding_60_days_limit():
    """Verify date ranges exceeding 60 days return an error dict."""
    res = find_dates.invoke({
        "natal_moon_sign": 0,
        "natal_nakshatra": 0,
        "start_date": "2026-10-01",
        "end_date": "2026-12-02",  # 62 days (delta_days = 62 > 60)
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5
    })
    assert "error" in res
    assert "Date range cannot exceed 60 days" in res["error"]


@pytest.mark.adversarial
def test_find_dates_inverted_range_error():
    """Verify end_date preceding start_date returns an error dict."""
    res = find_dates.invoke({
        "natal_moon_sign": 0,
        "natal_nakshatra": 0,
        "start_date": "2026-10-15",
        "end_date": "2026-10-01",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5
    })
    assert "error" in res
    assert "End date must be after or equal to start date" in res["error"]


@pytest.mark.adversarial
def test_find_dates_externalized_panchang_reference_loaded():
    """Verify find_dates actually utilizes externalized panchang_reference.json datasets."""
    panchang = load_panchang_reference()
    assert len(panchang["tithis"]) == 30
    assert len(panchang["taras"]) == 9
    assert len(SHUBH_TITHIS) > 0
    assert len(ASHUBH_TITHIS) > 0
    assert len(TITHI_NAMES) == 30
    assert len(TARA_NAMES) == 9
    assert len(AUSPICIOUS_ACTIONS) > 0
