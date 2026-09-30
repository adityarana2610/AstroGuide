import os
import json
import math
from datetime import datetime, timedelta
import swisseph as swe
try:
    from langchain_core.tools import tool
except (ImportError, ModuleNotFoundError):
    from astroguide.tools._decorator import tool

# Load Nakshatra table at module level
NAKSHATRA_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'tables', 'nakshatra_table.json')
with open(NAKSHATRA_FILE, 'r', encoding='utf-8') as f:
    _nakshatra_data = json.load(f)
NAKSHATRA_TABLE = _nakshatra_data.get("nakshatras", [])
NAKSHATRA_NAMES = [n["name"] for n in NAKSHATRA_TABLE]

RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def _format_planet_label(p: str) -> str:
    """Format planet abbreviation preserving (R) retrograde indicator."""
    prefix = p[:2]
    return f"{prefix}(R)" if "(R)" in p else prefix

def draw_north_indian_chart(houses_data, asc_sign_idx):
    """Generates an SVG for a North Indian style birth chart."""
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">']
    svg.append('<rect x="0" y="0" width="400" height="400" fill="white" stroke="black" stroke-width="2"/>')
    svg.append('<line x1="0" y1="0" x2="400" y2="400" stroke="black" stroke-width="2"/>')
    svg.append('<line x1="400" y1="0" x2="0" y2="400" stroke="black" stroke-width="2"/>')
    svg.append('<line x1="200" y1="0" x2="400" y2="200" stroke="black" stroke-width="2"/>')
    svg.append('<line x1="400" y1="200" x2="200" y2="400" stroke="black" stroke-width="2"/>')
    svg.append('<line x1="200" y1="400" x2="0" y2="200" stroke="black" stroke-width="2"/>')
    svg.append('<line x1="0" y1="200" x2="200" y2="0" stroke="black" stroke-width="2"/>')
    
    # House positions mapping in North Indian chart (x, y)
    h_centers = {
        1: (200, 100), 2: (100, 50), 3: (50, 100), 4: (100, 200),
        5: (50, 300), 6: (100, 350), 7: (200, 300), 8: (300, 350),
        9: (350, 300), 10: (300, 200), 11: (350, 100), 12: (300, 50)
    }
    
    for h_num, (cx, cy) in h_centers.items():
        house_info = next((h for h in houses_data if h["house_number"] == h_num), None)
        if house_info:
            sign_idx = (asc_sign_idx + h_num - 1) % 12
            svg.append(f'<text x="{cx}" y="{cy-15}" font-size="12" font-family="Arial" text-anchor="middle" fill="gray">{sign_idx + 1}</text>')
            planets_str = " ".join([_format_planet_label(p) for p in house_info["planets"]])
            if planets_str:
                svg.append(f'<text x="{cx}" y="{cy+10}" font-size="14" font-family="Arial" text-anchor="middle" font-weight="bold">{planets_str}</text>')
    
    svg.append('</svg>')
    return "".join(svg)


def draw_south_indian_chart(houses_data):
    """Generates an SVG for a South Indian style birth chart."""
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="100%" height="100%">']
    svg.append('<rect x="0" y="0" width="400" height="400" fill="white" stroke="black" stroke-width="2"/>')
    # Inner rectangle
    svg.append('<rect x="100" y="100" width="200" height="200" fill="white" stroke="black" stroke-width="2"/>')
    
    # Lines for grid
    svg.append('<line x1="100" y1="0" x2="100" y2="400" stroke="black" stroke-width="1"/>')
    svg.append('<line x1="200" y1="0" x2="200" y2="100" stroke="black" stroke-width="1"/>')
    svg.append('<line x1="300" y1="0" x2="300" y2="400" stroke="black" stroke-width="1"/>')
    
    svg.append('<line x1="0" y1="100" x2="400" y2="100" stroke="black" stroke-width="1"/>')
    svg.append('<line x1="0" y1="200" x2="100" y2="200" stroke="black" stroke-width="1"/>')
    svg.append('<line x1="300" y1="200" x2="400" y2="200" stroke="black" stroke-width="1"/>')
    svg.append('<line x1="0" y1="300" x2="400" y2="300" stroke="black" stroke-width="1"/>')
    
    svg.append('<line x1="200" y1="300" x2="200" y2="400" stroke="black" stroke-width="1"/>')

    # Mapping of Rashi names to grid locations (x, y) starting top-left
    # Pisces (0,0), Aries (1,0), Taurus (2,0), Gemini (3,0)
    # Aquarius (0,1)                           Cancer (3,1)
    # Capricorn (0,2)                          Leo (3,2)
    # Sagittarius (0,3), Scorpio (1,3), Libra (2,3), Virgo (3,3)
    rashi_centers = {
        11: (50, 50), 0: (150, 50), 1: (250, 50), 2: (350, 50),
        10: (50, 150),                            3: (350, 150),
        9: (50, 250),                             4: (350, 250),
        8: (50, 350), 7: (150, 350), 6: (250, 350), 5: (350, 350)
    }

    # First map planets and Ascendant to their signs
    sign_contents = {i: [] for i in range(12)}
    asc_sign_idx = -1
    for h in houses_data:
        s_name = h["sign"]
        s_idx = RASHI_NAMES.index(s_name)
        if h["house_number"] == 1:
            asc_sign_idx = s_idx
        for p in h["planets"]:
            sign_contents[s_idx].append(_format_planet_label(p))

    for s_idx, (cx, cy) in rashi_centers.items():
        if s_idx == asc_sign_idx:
            svg.append(f'<text x="{cx}" y="{cy-20}" font-size="12" font-family="Arial" text-anchor="middle" fill="red">Asc</text>')
        
        planets_str = " ".join(sign_contents[s_idx])
        if planets_str:
            svg.append(f'<text x="{cx}" y="{cy+10}" font-size="12" font-family="Arial" text-anchor="middle" font-weight="bold">{planets_str}</text>')
    
    svg.append('</svg>')
    return "".join(svg)


@tool
def get_birth_chart(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    tz_offset: float,
    chart_style: str,
    ayanamsha: str = "lahiri"
) -> dict:
    '''Computes a full Vedic (sidereal) birth chart using pyswisseph.

    Calculates planetary positions, ascendant, houses (whole-sign), nakshatras, 
    and generates an SVG visualization (North or South Indian style).

    Args:
        birth_date (str): Date of birth in YYYY-MM-DD format.
        birth_time (str): Time of birth in HH:MM format (24h).
        latitude (float): Latitude of birth location (decimal degrees).
        longitude (float): Longitude of birth location (decimal degrees).
        tz_offset (float): UTC offset in hours (e.g. 5.5 for IST).
        chart_style (str): "north" or "south" Indian style for SVG generation.
        ayanamsha (str): Sidereal ayanamsha. "lahiri", "raman", or "krishnamurti". Default is "lahiri".

    Returns:
        dict: Containing birth_info, ascendant, planets, houses, and svg_chart.
    '''
    try:
        dt = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Invalid date or time format. Use YYYY-MM-DD and HH:MM."}
    
    # Convert to UTC
    utc_dt = dt - timedelta(hours=tz_offset)
    
    # Calculate Julian Day
    utc_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_hour)
    
    # Set ayanamsha
    aya_map = {
        "lahiri": swe.SIDM_LAHIRI,
        "raman": swe.SIDM_RAMAN,
        "krishnamurti": swe.SIDM_KRISHNAMURTI
    }
    mode = aya_map.get(ayanamsha.lower(), swe.SIDM_LAHIRI)
    swe.set_sid_mode(mode)
    
    # Calculate Sidereal Ascendant
    aya = swe.get_ayanamsa_ut(jd)
    cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'W')
    trop_asc = ascmc[0]
    sid_asc = (trop_asc - aya) % 360.0
    
    asc_sign_idx = int(sid_asc / 30)
    asc_deg_in_sign = sid_asc % 30
    asc_nak_idx = int(sid_asc / (360/27.0))
    asc_pada = int((sid_asc % (360/27.0)) / (360/108.0)) + 1

    ascendant_info = {
        "sign": RASHI_NAMES[asc_sign_idx],
        "degree": round(asc_deg_in_sign, 3),
        "nakshatra": NAKSHATRA_NAMES[asc_nak_idx],
        "pada": asc_pada
    }
    
    # Planets calculation
    planet_ids = [
        ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
        ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER),
        ("Venus", swe.VENUS), ("Saturn", swe.SATURN),
        ("Rahu", swe.MEAN_NODE)
    ]
    
    planets_data = []
    
    for p_name, p_id in planet_ids:
        flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED
        res, ret = swe.calc_ut(jd, p_id, flags)
        lon = res[0]
        speed = res[3]
        
        sign_idx = int(lon / 30)
        deg_in_sign = lon % 30
        nak_idx = int(lon / (360/27.0))
        pada = int((lon % (360/27.0)) / (360/108.0)) + 1
        
        # Whole sign house: House 1 is ascendant's sign
        house_num = (sign_idx - asc_sign_idx) % 12 + 1
        
        is_retrograde = speed < 0 if p_name != "Rahu" else False
        
        planets_data.append({
            "name": p_name,
            "longitude": round(lon, 3),
            "sign": RASHI_NAMES[sign_idx],
            "sign_index": sign_idx,
            "degree_in_sign": round(deg_in_sign, 3),
            "nakshatra": NAKSHATRA_NAMES[nak_idx],
            "nakshatra_index": nak_idx,
            "pada": pada,
            "house": house_num,
            "is_retrograde": is_retrograde
        })
        
        if p_name == "Rahu":
            # Calculate Ketu
            ketu_lon = (lon + 180.0) % 360.0
            k_sign_idx = int(ketu_lon / 30)
            k_deg = ketu_lon % 30
            k_nak = int(ketu_lon / (360/27.0))
            k_pada = int((ketu_lon % (360/27.0)) / (360/108.0)) + 1
            k_house = (k_sign_idx - asc_sign_idx) % 12 + 1
            planets_data.append({
                "name": "Ketu",
                "longitude": round(ketu_lon, 3),
                "sign": RASHI_NAMES[k_sign_idx],
                "sign_index": k_sign_idx,
                "degree_in_sign": round(k_deg, 3),
                "nakshatra": NAKSHATRA_NAMES[k_nak],
                "nakshatra_index": k_nak,
                "pada": k_pada,
                "house": k_house,
                "is_retrograde": False
            })
            
    # Group by houses
    houses_data = []
    for h in range(1, 13):
        h_sign_idx = (asc_sign_idx + h - 1) % 12
        # Adding (R) suffix for retrograde planets
        h_planets = []
        for p in planets_data:
            if p["house"] == h:
                p_label = p["name"]
                if p.get("is_retrograde"):
                    p_label += "(R)"
                h_planets.append(p_label)
        houses_data.append({
            "house_number": h,
            "sign": RASHI_NAMES[h_sign_idx],
            "planets": h_planets
        })
        
    # Generate SVG
    if chart_style.lower() == "south":
        svg_chart = draw_south_indian_chart(houses_data)
    else:
        svg_chart = draw_north_indian_chart(houses_data, asc_sign_idx)
        
    return {
        "birth_info": {
            "date": birth_date,
            "time": birth_time,
            "lat": latitude,
            "lon": longitude,
            "tz_offset": tz_offset,
            "ayanamsha": ayanamsha
        },
        "ascendant": ascendant_info,
        "planets": planets_data,
        "houses": houses_data,
        "svg_chart": svg_chart
    }
