"""
geocode.py — Resolve a human-readable birth date/time/place into UTC datetime + coordinates.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


def resolve_birth_utc(
    date_str: str,
    time_str: str,
    place: str,
) -> tuple[datetime, float, float, str]:
    """Convert a birth date, time, and place into a UTC datetime with coordinates.

    Parameters
    ----------
    date_str : str
        Date in ``YYYY-MM-DD`` format.
    time_str : str
        Time in ``HH:MM`` (24-hour) format.
    place : str
        Human-readable place name (e.g. ``"Mumbai, India"``).

    Returns
    -------
    tuple[datetime, float, float, str]
        ``(utc_datetime, latitude, longitude, iana_timezone_name)``

    Raises
    ------
    ValueError
        If the place cannot be geocoded.
    """
    # --- geocode the place ------------------------------------------------
    geolocator = Nominatim(user_agent="astroguide-phase2")
    location = geolocator.geocode(place)
    if location is None:
        raise ValueError(
            f"Could not geocode place: {place!r}. "
            "Check spelling or try a more specific name."
        )

    lat, lon = location.latitude, location.longitude

    # --- determine IANA timezone ------------------------------------------
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError(
            f"Could not determine timezone for coordinates ({lat}, {lon})."
        )

    # --- build local datetime → convert to UTC ----------------------------
    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_dt = naive_dt.replace(tzinfo=ZoneInfo(tz_name))
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    return utc_dt, lat, lon, tz_name
