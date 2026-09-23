"""
tools.py — LangChain tools that wrap geocode, ephemeris, and numerology logic.
"""

import json
import os
from pathlib import Path

from langchain_core.tools import tool

from src.geocode import resolve_birth_utc
from src.ephemeris import compute_chart
from src.numerology import compute_numbers

# ── Module-level cache so the agent doesn't recompute charts ─────────────────
CHART_CACHE: dict[str, dict] = {}

# ── Load planet_map.json once ────────────────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
with open(_DATA_DIR / "planet_map.json", encoding="utf-8") as _f:
    PLANET_MAP: dict[str, dict] = json.load(_f)

# Reverse lookup: number → planet info
_NUMBER_TO_PLANET: dict[int, dict] = {
    info["number"]: {"planet": planet, **info}
    for planet, info in PLANET_MAP.items()
}


@tool
def get_birth_chart(name: str, date: str, time: str, place: str) -> dict:
    """Compute a Vedic (sidereal / Lahiri) birth chart.

    Parameters
    ----------
    name : str
        Person's name (used as cache key).
    date : str
        Date of birth in YYYY-MM-DD format, e.g. "1998-05-14".
    time : str
        Time of birth in HH:MM 24-hour format, e.g. "09:30".
    place : str
        Birth place, e.g. "Mumbai, India".

    Returns
    -------
    dict
        ``{name: str, positions: {planet: {sign, degree, retrograde, raw_longitude}}}``
    """
    if name in CHART_CACHE:
        return {"name": name, "positions": CHART_CACHE[name]}

    utc_dt, lat, lon, _tz = resolve_birth_utc(date, time, place)
    positions = compute_chart(utc_dt, lat, lon)
    CHART_CACHE[name] = positions
    return {"name": name, "positions": positions}


@tool
def get_numbers_and_stones(name: str, date: str) -> dict:
    """Compute Chaldean numerology numbers and suggest gemstones / colours.

    Parameters
    ----------
    name : str
        Person's full name.
    date : str
        Date of birth in YYYY-MM-DD format, e.g. "1998-05-14".

    Returns
    -------
    dict
        ``{life_path, birth_number, name_number, stone_hints: [...]}``
    """
    numbers = compute_numbers(name, date)

    # Map each computed number to its ruling planet's stone/colour
    stone_hints = []
    for label in ("life_path", "birth_number", "name_number"):
        num = numbers[label]
        planet_info = _NUMBER_TO_PLANET.get(num)
        if planet_info:
            stone_hints.append({
                "number_type": label,
                "value": num,
                "ruling_planet": planet_info["planet"],
                "stone": planet_info["stone"],
                "colour": planet_info["colour"],
                "day": planet_info["day"],
            })

    return {**numbers, "stone_hints": stone_hints}
