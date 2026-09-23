"""
ephemeris.py — Compute a sidereal (Lahiri) Vedic birth chart using the Swiss Ephemeris.
"""

from datetime import datetime

import swisseph as swe

# ── Sign names (0-indexed) ────────────────────────────────────────────────────
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# ── Planets to compute ───────────────────────────────────────────────────────
PLANETS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mars":    swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus":   swe.VENUS,
    "Saturn":  swe.SATURN,
    "Rahu":    swe.MEAN_NODE,       # mean lunar node
}


def compute_chart(utc_dt: datetime, lat: float, lon: float) -> dict:
    """Compute a sidereal Vedic birth chart.

    Parameters
    ----------
    utc_dt : datetime
        Birth moment in UTC (timezone-aware or naive-UTC).
    lat, lon : float
        Geographic latitude and longitude in decimal degrees.

    Returns
    -------
    dict
        Keys are planet names (including ``"Ketu"`` and ``"Ascendant"``).
        Each value is a dict with ``sign``, ``degree``, ``retrograde``.
    """
    # ── sidereal mode (Lahiri ayanamsa) ──────────────────────────────────
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # ── Julian day ───────────────────────────────────────────────────────
    jd = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )

    positions: dict[str, dict] = {}

    # ── planets ──────────────────────────────────────────────────────────
    for name, planet_id in PLANETS.items():
        lon_deg, speed = _calc_planet(jd, planet_id)
        positions[name] = _make_entry(lon_deg, speed)

    # ── Ketu (always 180° from Rahu) ─────────────────────────────────────
    rahu_lon = positions["Rahu"]["raw_longitude"]
    ketu_lon = (rahu_lon + 180.0) % 360.0
    positions["Ketu"] = _make_entry(ketu_lon, speed=0.0)

    # ── Ascendant (whole-sign houses) ────────────────────────────────────
    cusps, ascmc = swe.houses_ex(
        jd, lat, lon, b"W", swe.FLG_SIDEREAL,
    )
    asc_lon = ascmc[0]
    positions["Ascendant"] = _make_entry(asc_lon, speed=0.0)

    return positions


# ── helpers ──────────────────────────────────────────────────────────────────

def _calc_planet(jd: float, planet_id: int) -> tuple[float, float]:
    """Return (sidereal_longitude, daily_speed) for *planet_id*."""
    result, _ret_flag = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
    longitude = result[0]
    speed = result[3]
    return longitude, speed


def _make_entry(lon_deg: float, speed: float) -> dict:
    sign_index = int(lon_deg // 30) % 12
    degree_in_sign = round(lon_deg % 30, 4)
    return {
        "sign": SIGNS[sign_index],
        "degree": degree_in_sign,
        "retrograde": speed < 0,
        "raw_longitude": round(lon_deg, 4),
    }
