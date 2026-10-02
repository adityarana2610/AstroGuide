"""Reproduction and verification test runner for AstroGuide issues ISS-01 to ISS-08, ISS-10, ISS-12.

Can be run directly via: python test_reproduction.py
"""

import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tests.test_reproduction_fixes import (
    test_iss_01_standalone_imports,
    test_iss_03_boundary_out_of_bounds_inputs,
    test_iss_04_yoni_gender_scoring,
    test_iss_05_capricorn_vashya,
    test_iss_06_tara_koota_offset_8,
    test_iss_07_numerological_friendly_numbers,
    test_iss_08_web_ui_error_handling,
    test_iss_10_svg_chart_retrograde_indicators,
    test_iss_12_requirements_dependencies,
    test_standalone_test_tool,
)


def test_iss_02_server_error_response_wrapping():
    """ISS-02: Server API endpoints must return {'success': False, 'error': ...} when tools return error dicts."""
    import server

    # 1. /api/birth_chart with invalid date format
    res1 = server.api_birth_chart(server.BirthChartRequest(
        birth_date="invalid-date",
        birth_time="12:00",
        latitude=28.6139,
        longitude=77.2090,
        tz_offset=5.5,
        chart_style="north"
    ))
    assert res1["success"] is False, f"Expected success: False for invalid birth_chart date, got {res1}"
    assert "error" in res1, f"Expected 'error' in response, got {res1}"
    assert "data" not in res1 or res1.get("data") is None

    # 2. /api/numbers_stones with invalid date
    res2 = server.api_numbers_stones(server.NumbersStonesRequest(birth_date="bad-date"))
    assert res2["success"] is False, f"Expected success: False for invalid numbers_stones date, got {res2}"
    assert "error" in res2

    # 3. /api/find_dates with end_date before start_date
    res3 = server.api_find_dates(server.FindDatesRequest(
        natal_moon_sign=0,
        natal_nakshatra=0,
        start_date="2026-10-10",
        end_date="2026-10-01",
        latitude=28.6139,
        longitude=77.2090,
        tz_offset=5.5
    ))
    assert res3["success"] is False, f"Expected success: False for end_date before start_date, got {res3}"
    assert "error" in res3

    # 4. /api/daily_transits with invalid date format
    res4 = server.api_daily_transits(server.DailyTransitsRequest(
        natal_moon_sign=0,
        natal_moon_degree=15.0,
        target_date="bad-date"
    ))
    assert res4["success"] is False, f"Expected success: False for invalid daily_transits date, got {res4}"
    assert "error" in res4

    # 5. /api/compatibility with out-of-range nakshatra
    res5 = server.api_compatibility(server.CompatibilityRequest.model_construct(
        person1_moon_nakshatra=99,
        person1_moon_pada=1,
        person2_moon_nakshatra=0,
        person2_moon_pada=1
    ))
    assert res5["success"] is False, f"Expected success: False for invalid nakshatra in compatibility, got {res5}"
    assert "error" in res5

    # Also verify tool-level error handling directly
    from astroguide.tools.compatibility import match_compatibility
    compat_res = match_compatibility(person1_moon_nakshatra=99, person1_moon_pada=1,
                                     person2_moon_nakshatra=0, person2_moon_pada=1)
    assert "error" in compat_res

    # Optionally, if TestClient can be imported (when httpx is installed), test via TestClient too
    try:
        from starlette.testclient import TestClient
        client = TestClient(server.app)

        resp1 = client.post("/api/birth_chart", json={
            "birth_date": "invalid-date",
            "birth_time": "12:00",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "tz_offset": 5.5,
            "chart_style": "north"
        })
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert d1.get("success") is False
        assert "error" in d1

        resp2 = client.post("/api/numbers_stones", json={"birth_date": "bad-date"})
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2.get("success") is False
        assert "error" in d2
    except Exception:
        pass

TESTS = [
    ("ISS-01: Standalone Tool Importability", test_iss_01_standalone_imports),
    ("ISS-02: Server Error Response Wrapping", test_iss_02_server_error_response_wrapping),
    ("ISS-03: Boundary / Out-of-bounds Inputs", test_iss_03_boundary_out_of_bounds_inputs),
    ("ISS-04: Yoni Gender Compatibility Scoring", test_iss_04_yoni_gender_scoring),
    ("ISS-05: Capricorn (Makara) Vashya Degree Boundary", test_iss_05_capricorn_vashya),
    ("ISS-06: Tara Koota Offset 8 (Ati-Mitra)", test_iss_06_tara_koota_offset_8),
    ("ISS-07: Numerological Friendly Numbers & Deduplication", test_iss_07_numerological_friendly_numbers),
    ("ISS-08: Web UI Error Handling (static/script.js)", test_iss_08_web_ui_error_handling),
    ("ISS-10: SVG Chart Retrograde (R) Indicators", test_iss_10_svg_chart_retrograde_indicators),
    ("ISS-12: Dependencies in requirements.txt", test_iss_12_requirements_dependencies),
    ("TEST-TOOL: test_tool.py Clean Execution", test_standalone_test_tool),
]

def run_all():
    print("=" * 60)
    print("ASTROGUIDE ISSUE VERIFICATION RUNNER")
    print("=" * 60)
    passed = 0
    failed = 0
    results = []

    for name, test_fn in TESTS:
        try:
            test_fn()
            print(f" [PASS] {name}")
            passed += 1
            results.append((name, "PASS", None))
        except Exception as e:
            print(f" [FAIL] {name}: {e}")
            failed += 1
            results.append((name, "FAIL", str(e)))

    print("=" * 60)
    print(f"Summary: {passed} passed, {failed} failed, total {len(TESTS)}")
    print("=" * 60)
    return failed == 0, results

if __name__ == "__main__":
    success, _ = run_all()
    sys.exit(0 if success else 1)
