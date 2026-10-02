import json
import os
from datetime import datetime
from typing import Dict, Any, List

from astroguide.tools._decorator import tool

from astroguide.utils.data_loader import load_planet_stones, load_remedies, get_remedy_for_planet

# Load planet stone mappings and remedies via centralized cached data loader
PLANET_DATA = load_planet_stones()
REMEDIES_DATA = load_remedies()


def reduce_to_single_digit(n: int) -> int:
    """Reduces a number to a single digit by summing its digits repeatedly."""
    if n == 0:
        return 0
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n

@tool
def get_numbers_and_stones(birth_date: str) -> Dict[str, Any]:
    """
    Computes lucky number, lucky colour, and gemstone recommendation based on Vedic/Indian numerology.
    
    Args:
        birth_date: string (YYYY-MM-DD format) - The person's date of birth.
        
    Returns:
        JSON/dict containing driver and conductor numbers, driver and conductor planets,
        primary and secondary gemstones, lucky numbers, lucky colours, and friendly/unfriendly planets.
    """
    try:
        dt = datetime.strptime(birth_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM-DD."}
    
    day_str = f"{dt.day:02d}"
    driver_number = reduce_to_single_digit(dt.day)
    
    full_date_str = f"{dt.year:04d}{dt.month:02d}{dt.day:02d}"
    date_sum = sum(int(d) for d in full_date_str)
    conductor_number = reduce_to_single_digit(date_sum)
    
    driver_key = str(driver_number)
    conductor_key = str(conductor_number)
    
    driver_info = PLANET_DATA.get(driver_key, {})
    conductor_info = PLANET_DATA.get(conductor_key, {})
    
    driver_planet = driver_info.get("planet", "Unknown")
    conductor_planet = conductor_info.get("planet", "Unknown")
    
    primary_gemstone = driver_info.get("gemstone", "Unknown")
    secondary_gemstone = conductor_info.get("gemstone", "Unknown")
    
    lucky_colours = []
    if "colour" in driver_info:
        lucky_colours.append(driver_info["colour"])
    if "colour" in conductor_info and conductor_info["colour"] not in lucky_colours:
        lucky_colours.append(conductor_info["colour"])
        
    driver_friendly = set(driver_info.get("friendly_numbers", []))
    conductor_friendly = set(conductor_info.get("friendly_numbers", []))
    common_friendly = list(driver_friendly.intersection(conductor_friendly))
    
    lucky_numbers = [driver_number, conductor_number] + [n for n in common_friendly if n not in (driver_number, conductor_number)]
    lucky_numbers = list(dict.fromkeys(lucky_numbers))
    
    # We will return the driver's friendly/unfriendly planets for simplicity, or union
    friendly_planets = list(set(driver_info.get("friendly_planets", []) + conductor_info.get("friendly_planets", [])))
    unfriendly_planets = list(set(driver_info.get("unfriendly_planets", []) + conductor_info.get("unfriendly_planets", [])))
    
    # Enrich with comprehensive astrological remedies if available (Feature F1)
    remedies_dict = REMEDIES_DATA.get("remedies", REMEDIES_DATA) if isinstance(REMEDIES_DATA, dict) else {}
    driver_remedy = remedies_dict.get(driver_planet)
    conductor_remedy = remedies_dict.get(conductor_planet)

    response = {
        "birth_date": birth_date,
        "driver_number": driver_number,
        "driver_planet": driver_planet,
        "conductor_number": conductor_number,
        "conductor_planet": conductor_planet,
        "primary_gemstone": primary_gemstone,
        "secondary_gemstone": secondary_gemstone,
        "lucky_numbers": lucky_numbers,
        "lucky_colours": lucky_colours,
        "friendly_planets": sorted(friendly_planets),
        "unfriendly_planets": sorted(unfriendly_planets)
    }
    if driver_remedy:
        response["driver_remedy"] = driver_remedy
        response["driver_remedies"] = driver_remedy
    if conductor_remedy:
        response["conductor_remedy"] = conductor_remedy
        response["conductor_remedies"] = conductor_remedy

    return response


@tool
def get_astrological_remedy(planet_name: str) -> Dict[str, Any]:
    """
    Retrieves classical Vedic remedies, gemstones, mantras, and lifestyle actions for a given planet.
    
    Args:
        planet_name: Name of the planet (e.g., 'Sun', 'Saturn', 'Jupiter', 'Rahu').
        
    Returns:
        Dictionary containing remedy specifications for the planet.
    """
    rem = get_remedy_for_planet(planet_name)
    if not rem:
        return {"error": f"No remedies found for planet '{planet_name}'"}
    return rem

