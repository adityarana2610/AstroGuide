"""Comprehensive programmatic reproduction and verification test suite for AstroGuide.

Covers:
- ISS-01: Direct standalone import of tools without langchain_core
- ISS-02: Server API error response wrapping (success: False on tool errors)
- ISS-03: Boundary / Out-of-bounds inputs (sign 0-11, nakshatra 0-26)
- ISS-04: Yoni gender compatibility scoring (opposite-sex=4.0, same-sex=3.0)
- ISS-05: Capricorn (Makara) Vashya boundary (<15 deg Chatushpada, >=15 deg Jalachara)
- ISS-06: Tara Koota offset 8 (Ati-Mitra / Param Mitra favourable, full 3.0 pts)
- ISS-07: Numerological friendly numbers in JSON & lucky_numbers deduplication
- ISS-08: Web UI error handling in static/script.js (no 'Error: undefined')
- ISS-10: SVG chart retrograde (R) indicator preservation
- ISS-12: Requirements.txt contains fastapi, uvicorn, starlette, pydantic, pytest
"""

import sys
import os
import json
import subprocess
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# If langchain_core is not installed, provide temporary in-process mock for test setup
# Note: ISS-01 is tested in isolated subprocess to verify true standalone importability!
try:
    import langchain_core
except ImportError:
    class _MockTool:
        def __init__(self, func, name=None, description=None):
            self.func = func
            self.name = name or getattr(func, "__name__", "tool")
            self.description = description or getattr(func, "__doc__", "")
            self.__name__ = getattr(func, "__name__", self.name)
            self.__doc__ = getattr(func, "__doc__", self.description)
        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)
        def invoke(self, args, *_, **__):
            if isinstance(args, dict):
                return self.func(**args)
            return self.func(args)

    class _MockLangchainCoreTools:
        @staticmethod
        def tool(*args, **kwargs):
            if len(args) == 1 and callable(args[0]):
                return _MockTool(args[0])
            def wrapper(f):
                return _MockTool(f, kwargs.get("name"), kwargs.get("description"))
            return wrapper

    sys.modules['langchain_core'] = type('MockCore', (), {})()
    sys.modules['langchain_core.tools'] = _MockLangchainCoreTools


def test_iss_01_standalone_imports():
    """ISS-01: Direct standalone import of tools without langchain_core must succeed."""
    test_code = (
        "import sys\n"
        "from astroguide.tools.birth_chart import get_birth_chart\n"
        "from astroguide.tools.compatibility import match_compatibility\n"
        "from astroguide.tools.daily_transits import get_daily_transits\n"
        "from astroguide.tools.find_dates import find_dates\n"
        "from astroguide.tools.numbers_stones import get_numbers_and_stones\n"
        "from astroguide.tools import ALL_TOOLS\n"
        "assert len(ALL_TOOLS) == 5\n"
        "print('STANDALONE_IMPORT_SUCCESS')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", test_code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, (
        f"Standalone import failed with code {result.returncode}.\n"
        f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    assert "STANDALONE_IMPORT_SUCCESS" in result.stdout


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

    # Verify via HTTP TestClient
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




def test_iss_03_boundary_out_of_bounds_inputs():
    """ISS-03: Boundary / Out-of-bounds inputs for signs (0-11) and nakshatras (0-26).
    Must return graceful error dicts / responses and NOT crash with IndexError.
    """
    from astroguide.tools.daily_transits import get_daily_transits
    from astroguide.tools.find_dates import find_dates

    # 1. daily_transits with natal_moon_sign=12 (out of bounds)
    dt_res = get_daily_transits(natal_moon_sign=12, natal_moon_degree=15.0, target_date="2026-10-01")
    assert isinstance(dt_res, dict), "daily_transits must return a dictionary"
    assert "error" in dt_res, f"Expected error dict for natal_moon_sign=12, got: {dt_res}"

    # Also test negative sign
    dt_res_neg = get_daily_transits(natal_moon_sign=-1, natal_moon_degree=15.0, target_date="2026-10-01")
    assert "error" in dt_res_neg

    # 2. find_dates with natal_moon_sign=12
    fd_res_sign = find_dates(
        natal_moon_sign=12,
        natal_nakshatra=0,
        start_date="2026-10-01",
        end_date="2026-10-02",
        latitude=28.6139,
        longitude=77.2090,
        tz_offset=5.5
    )
    assert isinstance(fd_res_sign, dict)
    assert "error" in fd_res_sign, f"Expected error dict for natal_moon_sign=12 in find_dates, got: {fd_res_sign}"

    # 3. find_dates with natal_nakshatra=27
    fd_res_nak = find_dates(
        natal_moon_sign=0,
        natal_nakshatra=27,
        start_date="2026-10-01",
        end_date="2026-10-02",
        latitude=28.6139,
        longitude=77.2090,
        tz_offset=5.5
    )
    assert isinstance(fd_res_nak, dict)
    assert "error" in fd_res_nak, f"Expected error dict for natal_nakshatra=27 in find_dates, got: {fd_res_nak}"


def test_iss_04_yoni_gender_scoring():
    """ISS-04: Yoni gender scoring: male-female of same animal = 4.0, same-sex = 3.0."""
    from astroguide.tools.compatibility import match_compatibility

    # Ashwini (Nakshatra 0: Horse, Male) vs Shatabhisha (Nakshatra 23: Horse, Female)
    # Opposite genders of same animal -> Ideal marital union -> 4.0 points
    res_opp = match_compatibility(
        person1_moon_nakshatra=0,
        person1_moon_pada=1,
        person2_moon_nakshatra=23,
        person2_moon_pada=1
    )
    yoni_opp = next((k for k in res_opp["kootas"] if k["name"] == "Yoni"), None)
    assert yoni_opp is not None, "Yoni koota missing from result"
    assert yoni_opp["obtained"] == 4.0, (
        f"Expected 4.0 points for male-female pair of same animal (Horse), got {yoni_opp['obtained']}"
    )

    # Ashwini (Nakshatra 0: Horse, Male) vs Ashwini (Nakshatra 0: Horse, Male)
    # Same gender of same animal -> 3.0 points
    res_same = match_compatibility(
        person1_moon_nakshatra=0,
        person1_moon_pada=1,
        person2_moon_nakshatra=0,
        person2_moon_pada=1
    )
    yoni_same = next((k for k in res_same["kootas"] if k["name"] == "Yoni"), None)
    assert yoni_same is not None
    assert yoni_same["obtained"] == 3.0, (
        f"Expected 3.0 points for same-sex pair of same animal (Horse), got {yoni_same['obtained']}"
    )


def test_iss_05_capricorn_vashya():
    """ISS-05: Capricorn (Makara) Vashya: degree < 15 Chatushpada, degree >= 15 Jalachara."""
    from astroguide.tools.compatibility import get_moon_sign

    # Uttarashadha Pada 2 (Nakshatra 20, Pada 2):
    # total_padas = 20 * 4 + 1 = 81
    # sign_idx = 81 // 9 = 9 (Capricorn)
    # degree = 81 * 3.333 + 1.667 = 271.67 -> degree_in_sign = 1.67 (< 15)
    # First half of Makara (0-15 deg) is Chatushpada (quadruped, goat head)
    sign_info_first_half = get_moon_sign(nakshatra_idx=20, pada=2)
    assert sign_info_first_half["sign_idx"] == 9
    assert sign_info_first_half["vashya"] == "Chatushpada", (
        f"Expected Makara < 15 deg to be Chatushpada, got '{sign_info_first_half['vashya']}'"
    )

    # Dhanishta Pada 1 (Nakshatra 22, Pada 1):
    # total_padas = 22 * 4 + 0 = 88
    # sign_idx = 88 // 9 = 9 (Capricorn)
    # degree_in_sign = 25.0 deg (>= 15)
    # Second half of Makara (15-30 deg) is Jalachara (aquatic, crocodile tail)
    sign_info_second_half = get_moon_sign(nakshatra_idx=22, pada=1)
    assert sign_info_second_half["sign_idx"] == 9
    assert sign_info_second_half["vashya"] == "Jalachara", (
        f"Expected Makara >= 15 deg to be Jalachara, got '{sign_info_second_half['vashya']}'"
    )


def test_iss_06_tara_koota_offset_8():
    """ISS-06: Tara Koota: offset 8 (Ati-Mitra / Param Mitra) must be treated as favourable."""
    from astroguide.tools.compatibility import match_compatibility

    # Ashwini (0) vs Ashlesha (8)
    # t1 = (8 - 0) % 27 % 9 = 8 (Ati-Mitra / 9th Tara - auspicious)
    # t2 = (0 - 8) % 27 % 9 = 19 % 9 = 1 (Sampat / 2nd Tara - auspicious)
    # Both directions are favourable -> bilateral favourability -> full 3.0 points
    res = match_compatibility(
        person1_moon_nakshatra=0,
        person1_moon_pada=1,
        person2_moon_nakshatra=8,
        person2_moon_pada=1
    )
    tara_koota = next((k for k in res["kootas"] if k["name"] == "Tara"), None)
    assert tara_koota is not None, "Tara koota missing from result"
    assert tara_koota["obtained"] == 3.0, (
        f"Expected 3.0 points for Ati-Mitra (8) / Sampat (1) pair, got {tara_koota['obtained']}"
    )


def test_iss_07_numerological_friendly_numbers():
    """ISS-07: Numerological friendly numbers in table, populated common_friendly, deduplicated lucky_numbers."""
    # 1. Check data/tables/planet_stone_colour.json contains friendly_numbers for 1-9
    table_path = os.path.join(PROJECT_ROOT, "data", "tables", "planet_stone_colour.json")
    with open(table_path, "r", encoding="utf-8") as f:
        planet_data = json.load(f)

    for num in range(1, 10):
        key = str(num)
        assert key in planet_data, f"Key '{key}' missing from planet_stone_colour.json"
        assert "friendly_numbers" in planet_data[key], (
            f"friendly_numbers missing for number '{key}' in planet_stone_colour.json"
        )
        assert isinstance(planet_data[key]["friendly_numbers"], list), (
            f"friendly_numbers for '{key}' must be a list"
        )
        assert len(planet_data[key]["friendly_numbers"]) > 0, (
            f"friendly_numbers for '{key}' is empty"
        )

    # 2. Check get_numbers_and_stones common_friendly and lucky_numbers
    from astroguide.tools.numbers_stones import get_numbers_and_stones
    res = get_numbers_and_stones("1995-10-15")
    # driver = 1+5=6, conductor = 1+9+9+5+1+0+1+5 = 31 = 4
    # friendly numbers for 6 and 4 must intersect to produce auxiliary lucky numbers
    assert len(res["lucky_numbers"]) >= 2
    # Verify no duplicates
    assert len(res["lucky_numbers"]) == len(set(res["lucky_numbers"])), (
        f"Duplicates found in lucky_numbers: {res['lucky_numbers']}"
    )

    # 3. Check deduplication when driver == conductor
    # Date 2006-01-01 -> driver=1, conductor=1
    res_same = get_numbers_and_stones("2006-01-01")
    assert res_same["driver_number"] == 1
    assert res_same["conductor_number"] == 1
    assert res_same["lucky_numbers"].count(1) == 1, (
        f"lucky_numbers has duplicate '1': {res_same['lucky_numbers']}"
    )
    assert len(res_same["lucky_numbers"]) == len(set(res_same["lucky_numbers"]))


def test_iss_08_web_ui_error_handling():
    """ISS-08 & ISS-09: static/script.js properly handles errors without 'Error: undefined'."""
    script_path = os.path.join(PROJECT_ROOT, "static", "script.js")
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    # The script must inspect detail (e.g. FastAPI 422 validation detail array) or have fallback
    assert "detail" in content, "static/script.js does not handle 'detail' from FastAPI error responses"
    # Ensure it doesn't just do naive `Error: ${result.error}` without checking detail or fallback
    assert "Error: undefined" not in content


def test_iss_10_svg_chart_retrograde_indicators():
    """ISS-10: SVG chart preserves retrograde (R) indicators for retrograde planets."""
    from astroguide.tools.birth_chart import get_birth_chart

    # Date 2024-10-15 12:00 has retrograde planets (e.g. Jupiter, Saturn)
    chart = get_birth_chart(
        birth_date="2024-10-15",
        birth_time="12:00",
        latitude=28.6139,
        longitude=77.2090,
        tz_offset=5.5,
        chart_style="north"
    )

    # Confirm at least one planet is retrograde in planets list
    retro_planets = [p["name"] for p in chart["planets"] if p.get("is_retrograde")]
    assert len(retro_planets) > 0, "Expected at least one retrograde planet on 2024-10-15"

    # SVG chart must preserve (R) indicator
    svg = chart["svg_chart"]
    assert "(R)" in svg, f"SVG chart missing '(R)' retrograde indicators for {retro_planets}"

    # Also test south Indian chart
    chart_south = get_birth_chart(
        birth_date="2024-10-15",
        birth_time="12:00",
        latitude=28.6139,
        longitude=77.2090,
        tz_offset=5.5,
        chart_style="south"
    )
    assert "(R)" in chart_south["svg_chart"], "South Indian SVG chart missing '(R)' indicators"


def test_iss_12_requirements_dependencies():
    """ISS-12: requirements.txt must list fastapi, uvicorn, starlette, pydantic, pytest."""
    req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
    with open(req_path, "r", encoding="utf-8") as f:
        req_content = f.read().lower()

    required_packages = ["fastapi", "uvicorn", "starlette", "pydantic", "pytest"]
    for pkg in required_packages:
        assert pkg in req_content, f"Required package '{pkg}' missing from requirements.txt"


def test_standalone_test_tool():
    """Verify test_tool.py executes cleanly without import or runtime error."""
    result = subprocess.run(
        [sys.executable, "test_tool.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, (
        f"test_tool.py failed with exit code {result.returncode}.\n"
        f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    assert "Invoke worked" in result.stdout
    assert "Direct call worked" in result.stdout


if __name__ == "__main__":
    pytest.main(["-v", __file__])
