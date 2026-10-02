"""Shared pytest configuration, fixtures, and mock factories for AstroGuide test suite."""

import sys
import os
import json
import pytest

# Ensure project root is at the head of sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# If langchain_core is not present in the runtime environment,
# provide a lightweight mock so tool modules can be imported without dependency failures.
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


@pytest.fixture(scope="session")
def project_root():
    """Returns the absolute path to AstroGuide repository root."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def tables_data_dir(project_root):
    """Returns the absolute path to the data/tables directory."""
    return os.path.join(project_root, "data", "tables")


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient instance connected to server.app."""
    from starlette.testclient import TestClient
    import server
    return TestClient(server.app)


@pytest.fixture
def valid_birth_chart_payload():
    """Standard valid payload for /api/birth_chart endpoint and get_birth_chart tool."""
    return {
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5,
        "chart_style": "north",
        "ayanamsha": "lahiri"
    }


@pytest.fixture
def valid_numbers_stones_payload():
    """Standard valid payload for /api/numbers_stones endpoint and get_numbers_and_stones tool."""
    return {
        "birth_date": "1995-10-15"
    }


@pytest.fixture
def valid_find_dates_payload():
    """Standard valid payload for /api/find_dates endpoint and find_dates tool."""
    return {
        "natal_moon_sign": 0,
        "natal_nakshatra": 0,
        "start_date": "2026-10-01",
        "end_date": "2026-10-03",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "tz_offset": 5.5
    }


@pytest.fixture
def valid_daily_transits_payload():
    """Standard valid payload for /api/daily_transits endpoint and get_daily_transits tool."""
    return {
        "natal_moon_sign": 0,
        "natal_moon_degree": 15.0,
        "target_date": "2026-10-01"
    }


@pytest.fixture
def valid_compatibility_payload():
    """Standard valid payload for /api/compatibility endpoint and match_compatibility tool."""
    return {
        "person1_moon_nakshatra": 0,
        "person1_moon_pada": 1,
        "person2_moon_nakshatra": 3,
        "person2_moon_pada": 2
    }


@pytest.fixture
def temp_data_dir(tmp_path):
    """Creates a temporary, isolated tables directory with mock reference tables for testing."""
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    # 1. Mock gochara_rules.json
    gochara_data = {
        "Sun": {
            "favourable_houses": [3, 6, 10, 11],
            "unfavourable_houses": [1, 2, 4, 5, 7, 8, 9, 12],
            "vedha_pairs": {"3": 9, "6": 12, "10": 4, "11": 5}
        },
        "Moon": {
            "favourable_houses": [1, 3, 6, 7, 10, 11],
            "unfavourable_houses": [2, 4, 5, 8, 9, 12],
            "vedha_pairs": {"1": 5, "3": 9, "6": 12, "7": 2, "10": 4, "11": 8}
        }
    }
    (tables_dir / "gochara_rules.json").write_text(
        json.dumps(gochara_data, indent=2), encoding="utf-8"
    )

    # 2. Mock nakshatra_table.json
    nakshatra_data = {
        "nakshatras": [
            {
                "index": 0,
                "name": "Ashwini",
                "start_degree": 0.0,
                "end_degree": 13.333,
                "ruler": "Ketu",
                "deity": "Ashwini Kumaras",
                "gana": "Deva",
                "yoni": "Horse",
                "yoni_type": "Male",
                "nadi": "Vata",
                "varna": "Vaishya",
                "sign": "Aries",
                "sign_lord": "Mars"
            },
            {
                "index": 1,
                "name": "Bharani",
                "start_degree": 13.333,
                "end_degree": 26.667,
                "ruler": "Venus",
                "deity": "Yama",
                "gana": "Manushya",
                "yoni": "Elephant",
                "yoni_type": "Male",
                "nadi": "Pitta",
                "varna": "Mlechha",
                "sign": "Aries",
                "sign_lord": "Mars"
            }
        ],
        "yoni_compatibility": {
            "Horse": "Buffalo",
            "Buffalo": "Horse",
            "Elephant": "Lion",
            "Lion": "Elephant"
        }
    }
    (tables_dir / "nakshatra_table.json").write_text(
        json.dumps(nakshatra_data, indent=2), encoding="utf-8"
    )

    # 3. Mock planet_stone_colour.json
    planet_data = {
        "1": {
            "planet": "Sun",
            "gemstone": "Ruby",
            "colour": "Red",
            "friendly_planets": ["Moon", "Mars", "Jupiter"],
            "unfriendly_planets": ["Venus", "Saturn"],
            "friendly_numbers": [1, 2, 3, 9]
        },
        "2": {
            "planet": "Moon",
            "gemstone": "Pearl",
            "colour": "White",
            "friendly_planets": ["Sun", "Mercury"],
            "unfriendly_planets": ["Rahu", "Ketu"],
            "friendly_numbers": [1, 2, 5]
        }
    }
    (tables_dir / "planet_stone_colour.json").write_text(
        json.dumps(planet_data, indent=2), encoding="utf-8"
    )

    # 4. Mock astrological_remedies.json
    remedies_data = {
        "remedies": {
            "Sun": {
                "planet": "Sun",
                "primary_gemstone": "Ruby",
                "substitute_gemstone": "Red Garnet",
                "metal": "Gold or Copper",
                "wear_finger": "Ring Finger",
                "wear_day": "Sunday morning",
                "mantra": "Om Hram Hreem Hroum Sah Suryaya Namah",
                "deity": "Lord Surya",
                "rudraksha": "1 Mukhi or 12 Mukhi",
                "charity_items": ["Wheat", "Copper", "Jaggery", "Red cloth"],
                "fasting_day": "Sunday",
                "positive_lifestyle_action": "Practice Surya Namaskar at dawn"
            }
        }
    }
    (tables_dir / "astrological_remedies.json").write_text(
        json.dumps(remedies_data, indent=2), encoding="utf-8"
    )

    return tables_dir
