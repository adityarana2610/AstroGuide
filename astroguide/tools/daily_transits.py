import json
import os
import datetime
from typing import Optional

try:
    from langchain_core.tools import tool
except (ImportError, ModuleNotFoundError):
    from astroguide.tools._decorator import tool
import swisseph as swe

RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

PLANET_NAMES = {
    swe.SUN: "Sun",
    swe.MOON: "Moon",
    swe.MARS: "Mars",
    swe.MERCURY: "Mercury",
    swe.JUPITER: "Jupiter",
    swe.VENUS: "Venus",
    swe.SATURN: "Saturn",
    swe.MEAN_NODE: "Rahu",
}

PLANET_KEYS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

from astroguide.utils.data_loader import load_gochara_rules

def get_gochara_rules() -> dict:
    """Returns cached Gochara transit rules and Vedha pairs."""
    return load_gochara_rules()


@tool
def get_daily_transits(natal_moon_sign: int, natal_moon_degree: float = 0.0, target_date: Optional[str] = None) -> dict:
    """
    Computes current planetary transits and scores them against the natal Moon sign using traditional Vedic Gochara rules with Vedha checks.
    
    Args:
        natal_moon_sign (int): Rashi index of natal Moon (0=Aries, 1=Taurus, ..., 11=Pisces).
        natal_moon_degree (float): Exact sidereal degree of natal Moon (0 to 360).
        target_date (str, optional): Date to compute transits for in YYYY-MM-DD format. Defaults to today if empty or None.
        
    Returns:
        dict: A JSON-serializable dictionary containing the date, natal_moon_sign, detailed transit information for each planet (longitude, sign, house_from_moon, is_favourable, vedha_blocked, score, etc.), overall score, and a day rating summary.
    """
    if not isinstance(natal_moon_sign, int) or natal_moon_sign < 0 or natal_moon_sign > 11:
        return {"error": f"Invalid natal_moon_sign '{natal_moon_sign}'. Must be an integer between 0 and 11."}

    if not target_date:
        target_date = datetime.date.today().strftime('%Y-%m-%d')
        
    try:
        dt = datetime.datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        return {"error": f"Invalid date format for target_date '{target_date}'. Expected YYYY-MM-DD."}
    
    # Calculate Julian day for 12:00 UTC
    year, month, day = dt.year, dt.month, dt.day
    hour = 12.0
    jd = swe.julday(year, month, day, hour)
    
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    planets = [swe.SUN, swe.MOON, swe.MARS, swe.MERCURY, swe.JUPITER, swe.VENUS, swe.SATURN, swe.MEAN_NODE]
    
    transit_positions = {}
    for p in planets:
        res, _ = swe.calc_ut(jd, p, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        lon = res[0]
        transit_positions[PLANET_NAMES[p]] = lon
        
    # Calculate Ketu
    rahu_lon = transit_positions["Rahu"]
    ketu_lon = (rahu_lon + 180.0) % 360.0
    transit_positions["Ketu"] = ketu_lon
    
    gochara_rules = get_gochara_rules()
    
    # Pre-calculate planet signs and houses
    planet_house_map = {}
    
    for p_name in PLANET_KEYS:
        lon = transit_positions[p_name]
        sign_idx = int(lon / 30.0)
        house_from_moon = ((sign_idx - natal_moon_sign) % 12) + 1
        planet_house_map[p_name] = house_from_moon
        
    transits = []
    favourable_count = 0
    blocked_count = 0
    unfavourable_count = 0
    overall_score = 0
    
    for p_name in PLANET_KEYS:
        lon = transit_positions[p_name]
        sign_idx = int(lon / 30.0)
        house_from_moon = planet_house_map[p_name]
        
        is_favourable = False
        vedha_blocked = False
        vedha_blocked_by = None
        score = -1
        
        rules = gochara_rules.get(p_name, {})
        favourable = rules.get("favourable_houses", [])
        vedha_pairs = rules.get("vedha_pairs", {})
        
        if house_from_moon in favourable:
            is_favourable = True
            vedha_house = vedha_pairs.get(str(house_from_moon))
            
            # Check Vedha: is ANY other planet in the vedha_house?
            if vedha_house is not None:
                for other_p, other_h in planet_house_map.items():
                    if other_p != p_name and other_h == vedha_house:
                        vedha_blocked = True
                        vedha_blocked_by = other_p
                        break
            
            if vedha_blocked:
                score = 0
                blocked_count += 1
            else:
                score = 1
                favourable_count += 1
        else:
            unfavourable_count += 1
            
        overall_score += score
        
        transits.append({
            "planet": p_name,
            "longitude": round(lon, 3),
            "sign": RASHI_NAMES[sign_idx],
            "house_from_moon": house_from_moon,
            "is_favourable": is_favourable,
            "vedha_blocked": vedha_blocked,
            "vedha_blocked_by": vedha_blocked_by,
            "score": score
        })
        
    day_rating = ""
    if overall_score >= 3:
        day_rating = "Highly Favourable"
    elif overall_score >= 1:
        day_rating = "Favourable"
    elif overall_score == 0:
        day_rating = "Neutral"
    elif overall_score >= -2:
        day_rating = "Challenging"
    else:
        day_rating = "Difficult"
        
    summary = f"{favourable_count} planets in favourable positions, {blocked_count} blocked by Vedha, {unfavourable_count} unfavourable"
    
    return {
        "date": target_date,
        "natal_moon_sign": RASHI_NAMES[natal_moon_sign],
        "transits": transits,
        "overall_score": overall_score,
        "day_rating": day_rating,
        "summary": summary
    }
