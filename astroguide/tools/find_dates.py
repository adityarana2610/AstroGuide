import math
import datetime
from typing import Dict, Any, List
import swisseph as swe
try:
    from langchain_core.tools import tool
except (ImportError, ModuleNotFoundError):
    from astroguide.tools._decorator import tool

RASHI_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", 
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", 
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", 
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", 
    "Uttara Bhadrapada", "Revati"
]
TARA_NAMES = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyari", "Sadhaka", "Vadha", "Mitra", "Ati-Mitra"]
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", 
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", 
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima", 
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", 
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", 
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

SHUBH_TITHIS = {2, 3, 5, 7, 10, 11, 13, 15, 17, 18, 20, 22, 25, 26, 28}
ASHUBH_TITHIS = {4, 8, 9, 14, 19, 23, 24, 29, 30}

AUSPICIOUS_ACTIONS = [
    "An excellent day for new beginnings and important decisions.",
    "Ideal for initiating long-term projects and signing contracts.",
    "A wonderful time for celebrations and significant purchases.",
    "Great for starting new educational pursuits or investments.",
    "Favorable for important meetings and spiritual practices."
]

NEUTRAL_ACTIONS = [
    "A good day for routine tasks and personal reflection.",
    "Focus on maintaining current projects and steady progress.",
    "Ideal for organizing, planning, and consolidating resources.",
    "Favorable for catching up on administrative work.",
    "A suitable day for quiet work and attending to details."
]

INAUSPICIOUS_ACTIONS = [
    "Focus on completing ongoing projects and nurturing relationships.",
    "Best to avoid major new initiatives today.",
    "A day for reflection, meditation, and finishing pending tasks.",
    "Exercise caution in financial dealings and travel.",
    "Keep a low profile and avoid aggressive moves."
]

@tool
def find_dates(natal_moon_sign: int, natal_nakshatra: int, start_date: str, end_date: str, latitude: float, longitude: float, tz_offset: float) -> Dict[str, Any]:
    """
    Evaluate a date range and score each day as auspicious/inauspicious based on Tithi, Chandrabala, Tarabala, and Rahu Kalam.
    
    Args:
        natal_moon_sign (int): Rashi index of natal Moon (0-11, where 0=Aries).
        natal_nakshatra (int): Nakshatra index of natal Moon (0-26).
        start_date (str): Start of evaluation range in YYYY-MM-DD format.
        end_date (str): End of evaluation range in YYYY-MM-DD format.
        latitude (float): Location latitude.
        longitude (float): Location longitude.
        tz_offset (float): UTC offset in hours.
        
    Returns:
        Dict containing astrological analysis of the dates in the range, the best dates, and dates to avoid.
    """
    if not isinstance(natal_moon_sign, int) or natal_moon_sign < 0 or natal_moon_sign > 11:
        return {"error": f"Invalid natal_moon_sign '{natal_moon_sign}'. Must be an integer between 0 and 11."}
    if not isinstance(natal_nakshatra, int) or natal_nakshatra < 0 or natal_nakshatra > 26:
        return {"error": f"Invalid natal_nakshatra '{natal_nakshatra}'. Must be an integer between 0 and 26."}

    try:
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}
        
    if end_dt < start_dt:
        return {"error": "End date must be after or equal to start date."}
        
    delta_days = (end_dt - start_dt).days
    if delta_days > 60:
        return {"error": "Date range cannot exceed 60 days."}
        
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    dates_list = []
    best_dates = []
    dates_to_avoid = []
    
    # Rahu Kalam standard period indices (0-based) for Mon-Sun
    rahu_periods = [1, 6, 4, 5, 3, 2, 7]
    
    for i in range(delta_days + 1):
        curr_dt = start_dt + datetime.timedelta(days=i)
        
        # Calculate noon UTC based on timezone
        local_noon = datetime.datetime(curr_dt.year, curr_dt.month, curr_dt.day, 12, 0, 0)
        utc_noon = local_noon - datetime.timedelta(hours=tz_offset)
        
        jd = swe.julday(utc_noon.year, utc_noon.month, utc_noon.day, utc_noon.hour + utc_noon.minute / 60.0)
        
        moon_pos, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
        sun_pos, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
        moon_long = moon_pos[0]
        sun_long = sun_pos[0]
        
        # 1. Tithi
        diff = (moon_long - sun_long) % 360
        tithi_num = int(diff / 12) + 1
        tithi_name = TITHI_NAMES[tithi_num - 1]
        paksha = "Shukla" if tithi_num <= 15 else "Krishna"
        tithi_is_ausp = tithi_num in SHUBH_TITHIS
        tithi_score = 2 if tithi_is_ausp else (-2 if tithi_num in ASHUBH_TITHIS else 0)
        
        # 2. Chandrabala
        transit_moon_sign = int(moon_long / 30)
        house_from_natal = ((transit_moon_sign - natal_moon_sign) % 12) + 1
        chandrabala_favourable = house_from_natal in {1, 3, 6, 7, 10, 11}
        chandrabala_score = 1 if chandrabala_favourable else -1
        
        # 3. Tarabala
        transit_nak = int(moon_long / (360 / 27.0))
        count_from_birth = ((transit_nak - natal_nakshatra) % 27) + 1
        tara_num = ((count_from_birth - 1) % 9) + 1
        tara_name = TARA_NAMES[tara_num - 1]
        tarabala_favourable = tara_num in {2, 4, 6, 8, 9}
        tarabala_score = 1 if tarabala_favourable else -1
        
        # 4. Rahu Kalam
        weekday = curr_dt.weekday() # Mon=0, Sun=6
        period_idx = rahu_periods[weekday]
        start_hr = 6.0 + period_idx * 1.5
        end_hr = start_hr + 1.5
        
        def format_hr(h: float) -> str:
            h_int = int(h)
            m_int = int(round((h - h_int) * 60))
            return f"{h_int:02d}:{m_int:02d}"
            
        rahu_start = format_hr(start_hr)
        rahu_end = format_hr(end_hr)
        
        # 5. Composite Score
        composite_score = tithi_score + chandrabala_score + tarabala_score
        is_auspicious = composite_score >= 2
        is_avoid = composite_score <= -2
        
        if is_auspicious:
            positive_action = AUSPICIOUS_ACTIONS[i % len(AUSPICIOUS_ACTIONS)]
            best_dates.append(curr_dt.strftime("%Y-%m-%d"))
        elif is_avoid:
            positive_action = INAUSPICIOUS_ACTIONS[i % len(INAUSPICIOUS_ACTIONS)]
            dates_to_avoid.append(curr_dt.strftime("%Y-%m-%d"))
        else:
            positive_action = NEUTRAL_ACTIONS[i % len(NEUTRAL_ACTIONS)]
            
        dates_list.append({
            "date": curr_dt.strftime("%Y-%m-%d"),
            "day_of_week": curr_dt.strftime("%A"),
            "tithi": {
                "number": tithi_num,
                "name": tithi_name,
                "paksha": paksha,
                "is_auspicious": tithi_is_ausp
            },
            "chandrabala": {
                "transit_moon_sign": RASHI_NAMES[transit_moon_sign],
                "house_from_natal": house_from_natal,
                "is_favourable": chandrabala_favourable
            },
            "tarabala": {
                "transit_nakshatra": NAKSHATRA_NAMES[transit_nak],
                "tara_number": tara_num,
                "tara_name": tara_name,
                "is_favourable": tarabala_favourable
            },
            "rahu_kalam": {
                "start": rahu_start,
                "end": rahu_end
            },
            "composite_score": composite_score,
            "is_auspicious": is_auspicious,
            "positive_action": positive_action
        })
        
    return {
        "date_range": {"start": start_date, "end": end_date},
        "natal_info": {
            "moon_sign": RASHI_NAMES[natal_moon_sign],
            "nakshatra": NAKSHATRA_NAMES[natal_nakshatra]
        },
        "dates": dates_list,
        "best_dates": best_dates,
        "dates_to_avoid": dates_to_avoid
    }
