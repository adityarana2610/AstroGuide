import json
import os
try:
    from langchain_core.tools import tool
except (ImportError, ModuleNotFoundError):
    from astroguide.tools._decorator import tool

from astroguide.utils.data_loader import load_nakshatra_table

# Load nakshatra table and yoni rules via centralized cached data loader (enforces UTF-8)
_NAKSHATRA_DATA = load_nakshatra_table()
NAKSHATRAS = _NAKSHATRA_DATA.get('nakshatras', [])
YONI_ENEMIES = _NAKSHATRA_DATA.get('yoni_compatibility', _NAKSHATRA_DATA.get('yoni_enemies', {}))


SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", 
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
]

# Planetary friendships
PLANET_FRIENDS = {
    "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "neutrals": ["Mercury"], "enemies": ["Venus", "Saturn"]},
    "Moon": {"friends": ["Sun", "Mercury"], "neutrals": ["Mars", "Jupiter", "Venus", "Saturn"], "enemies": []},
    "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "neutrals": ["Venus", "Saturn"], "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun", "Venus"], "neutrals": ["Mars", "Jupiter", "Saturn"], "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "neutrals": ["Saturn"], "enemies": ["Mercury", "Venus"]},
    "Venus": {"friends": ["Mercury", "Saturn"], "neutrals": ["Mars", "Jupiter"], "enemies": ["Sun", "Moon"]},
    "Saturn": {"friends": ["Mercury", "Venus"], "neutrals": ["Jupiter"], "enemies": ["Sun", "Moon", "Mars"]}
}

def get_moon_sign(nakshatra_idx: int, pada: int) -> dict:
    # Total padas from Ashwini pada 1
    total_padas = nakshatra_idx * 4 + (pada - 1)
    sign_idx = total_padas // 9
    
    degree = total_padas * (10 / 3) + (5 / 3)
    degree_in_sign = degree % 30
    
    varna = [3, 2, 1, 4, 3, 2, 1, 4, 3, 2, 1, 4][sign_idx]
    
    if sign_idx == 0: vashya = "Chatushpada"
    elif sign_idx == 1: vashya = "Chatushpada"
    elif sign_idx == 2: vashya = "Dwipad"
    elif sign_idx == 3: vashya = "Jalachara"
    elif sign_idx == 4: vashya = "Vanachara"
    elif sign_idx == 5: vashya = "Dwipad"
    elif sign_idx == 6: vashya = "Dwipad"
    elif sign_idx == 7: vashya = "Keeta"
    elif sign_idx == 8: vashya = "Dwipad" if degree_in_sign < 15 else "Chatushpada"
    elif sign_idx == 9: vashya = "Chatushpada" if degree_in_sign < 15 else "Jalachara"
    elif sign_idx == 10: vashya = "Dwipad"
    else: vashya = "Jalachara"
    
    return {
        "sign_idx": sign_idx,
        "name": SIGN_NAMES[sign_idx],
        "lord": SIGN_LORDS[sign_idx],
        "varna": varna,
        "vashya": vashya
    }

def score_vashya(v1: str, v2: str) -> float:
    if v1 == v2:
        return 2.0
    # Simplified vashya scoring rules as requested: Same=2, Enemy=0, else=1
    # Standard enemies
    enemies = [
        {"Chatushpada", "Vanachara"}, 
        {"Dwipad", "Chatushpada"},
        {"Jalachara", "Vanachara"}
    ]
    if {v1, v2} in enemies:
        return 0.0
    return 1.0

@tool
def match_compatibility(person1_moon_nakshatra: int, person1_moon_pada: int, person2_moon_nakshatra: int, person2_moon_pada: int) -> dict:
    """
    Computes the full Ashtakoota (8-Koota) Guna Milan compatibility score between two individuals.
    
    Args:
        person1_moon_nakshatra (int): Nakshatra index of person 1's Moon (0-26).
        person1_moon_pada (int): Pada of person 1's Moon (1-4).
        person2_moon_nakshatra (int): Nakshatra index of person 2's Moon (0-26).
        person2_moon_pada (int): Pada of person 2's Moon (1-4).
        
    Returns:
        dict: Detailed compatibility score across all 8 Kootas.
    """
    if not (0 <= person1_moon_nakshatra <= 26) or not (0 <= person2_moon_nakshatra <= 26):
        return {"error": "Nakshatra index must be between 0 and 26"}
    if not (1 <= person1_moon_pada <= 4) or not (1 <= person2_moon_pada <= 4):
        return {"error": "Pada must be between 1 and 4"}
        
    p1_sign_info = get_moon_sign(person1_moon_nakshatra, person1_moon_pada)
    p2_sign_info = get_moon_sign(person2_moon_nakshatra, person2_moon_pada)
    
    p1_nak_info = NAKSHATRAS[person1_moon_nakshatra]
    p2_nak_info = NAKSHATRAS[person2_moon_nakshatra]
    
    kootas = []
    total_score = 0.0
    
    # 1. Varna (Max 1)
    # p1 = groom, p2 = bride
    varna_score = 1.0 if p1_sign_info["varna"] >= p2_sign_info["varna"] else 0.0
    kootas.append({
        "name": "Varna", 
        "max_points": 1, 
        "obtained": varna_score, 
        "description": f"Person 1 Varna {p1_sign_info['varna']}, Person 2 Varna {p2_sign_info['varna']}"
    })
    total_score += varna_score
    
    # 2. Vashya (Max 2)
    vashya_score = score_vashya(p1_sign_info["vashya"], p2_sign_info["vashya"])
    kootas.append({
        "name": "Vashya", 
        "max_points": 2, 
        "obtained": vashya_score, 
        "description": f"Person 1: {p1_sign_info['vashya']}, Person 2: {p2_sign_info['vashya']}"
    })
    total_score += vashya_score
    
    # 3. Tara (Max 3)
    t1 = ((person2_moon_nakshatra - person1_moon_nakshatra) % 27) % 9
    t2 = ((person1_moon_nakshatra - person2_moon_nakshatra) % 27) % 9
    
    t1_fav = t1 in {1, 3, 5, 7, 8}
    t2_fav = t2 in {1, 3, 5, 7, 8}
    if t1_fav and t2_fav: tara_score = 3.0
    elif t1_fav or t2_fav: tara_score = 1.5
    else: tara_score = 0.0
    kootas.append({
        "name": "Tara", 
        "max_points": 3, 
        "obtained": tara_score, 
        "description": f"Tara remainders: {t1}, {t2}"
    })
    total_score += tara_score
    
    # 4. Yoni (Max 4)
    y1_animal = p1_nak_info.get("yoni", p1_nak_info.get("yoni_animal", ""))
    y2_animal = p2_nak_info.get("yoni", p2_nak_info.get("yoni_animal", ""))
    y1_gender = p1_nak_info.get("yoni_type", p1_nak_info.get("yoni_gender", ""))
    y2_gender = p2_nak_info.get("yoni_type", p2_nak_info.get("yoni_gender", ""))
    
    if y1_animal == y2_animal:
        yoni_score = 3.0 if y1_gender == y2_gender else 4.0
    elif YONI_ENEMIES.get(y1_animal) == y2_animal:
        yoni_score = 0.0
    else:
        # Simplified: fallback to neutral
        yoni_score = 1.0
        
    kootas.append({
        "name": "Yoni", 
        "max_points": 4, 
        "obtained": yoni_score, 
        "description": f"{y1_animal}({y1_gender}) vs {y2_animal}({y2_gender})"
    })
    total_score += yoni_score
    
    # 5. Graha Maitri (Max 5)
    l1 = p1_sign_info["lord"]
    l2 = p2_sign_info["lord"]
    
    def get_relationship(planet1, planet2):
        if planet1 == planet2:
            return "Friend"
        rels = PLANET_FRIENDS[planet1]
        if planet2 in rels["friends"]: return "Friend"
        if planet2 in rels["neutrals"]: return "Neutral"
        return "Enemy"
        
    r1 = get_relationship(l1, l2)
    r2 = get_relationship(l2, l1)
    
    if r1 == "Friend" and r2 == "Friend": graha_score = 5.0
    elif (r1 == "Friend" and r2 == "Neutral") or (r2 == "Friend" and r1 == "Neutral"): graha_score = 4.0
    elif r1 == "Neutral" and r2 == "Neutral": graha_score = 3.0
    elif (r1 == "Friend" and r2 == "Enemy") or (r2 == "Friend" and r1 == "Enemy"): graha_score = 1.0
    elif (r1 == "Neutral" and r2 == "Enemy") or (r2 == "Neutral" and r1 == "Enemy"): graha_score = 0.5
    else: graha_score = 0.0
    
    kootas.append({
        "name": "Graha Maitri", 
        "max_points": 5, 
        "obtained": graha_score, 
        "description": f"{l1} ({r1}) vs {l2} ({r2})"
    })
    total_score += graha_score
    
    # 6. Gana (Max 6)
    g1 = p1_nak_info["gana"]
    g2 = p2_nak_info["gana"]
    if g1 == g2: gana_score = 6.0
    elif {g1, g2} == {"Deva", "Manushya"}: gana_score = 5.0
    elif g1 == "Deva" and g2 == "Rakshasa": gana_score = 0.0
    elif g1 == "Rakshasa" and g2 == "Deva": gana_score = 1.0
    else: gana_score = 0.0 # Manushya-Rakshasa(0), Rakshasa-Manushya(0)
    
    kootas.append({
        "name": "Gana", 
        "max_points": 6, 
        "obtained": gana_score, 
        "description": f"Person 1: {g1}, Person 2: {g2}"
    })
    total_score += gana_score
    
    # 7. Bhakoot (Max 7)
    s1 = p1_sign_info["sign_idx"]
    s2 = p2_sign_info["sign_idx"]
    diff = (s2 - s1) % 12 + 1
    
    bad_diffs = {2, 12, 6, 8, 5, 9}
    if diff in bad_diffs:
        bhakoot_score = 0.0
        bhakoot_dosha = True
    else:
        bhakoot_score = 7.0
        bhakoot_dosha = False
        
    kootas.append({
        "name": "Bhakoot", 
        "max_points": 7, 
        "obtained": bhakoot_score, 
        "description": f"Sign distance: {diff}"
    })
    total_score += bhakoot_score
    
    # 8. Nadi (Max 8)
    n1 = p1_nak_info["nadi"]
    n2 = p2_nak_info["nadi"]
    if n1 == n2:
        nadi_score = 0.0
        nadi_dosha = True
    else:
        nadi_score = 8.0
        nadi_dosha = False
        
    kootas.append({
        "name": "Nadi", 
        "max_points": 8, 
        "obtained": nadi_score, 
        "description": f"Person 1: {n1}, Person 2: {n2}"
    })
    total_score += nadi_score
    
    if total_score >= 28: rating = "Excellent"
    elif total_score >= 21: rating = "Good"
    elif total_score >= 18: rating = "Average"
    else: rating = "Below Average"
    
    return {
        "person1": {
            "nakshatra": p1_nak_info["name"],
            "pada": person1_moon_pada,
            "sign": p1_sign_info["name"],
            "sign_lord": p1_sign_info["lord"]
        },
        "person2": {
            "nakshatra": p2_nak_info["name"],
            "pada": person2_moon_pada,
            "sign": p2_sign_info["name"],
            "sign_lord": p2_sign_info["lord"]
        },
        "kootas": kootas,
        "total_score": total_score,
        "max_score": 36,
        "compatibility_rating": rating,
        "rating_thresholds": {
            "Excellent": ">=28", 
            "Good": ">=21", 
            "Average": ">=18", 
            "Below Average": "<18"
        },
        "nadi_dosha": nadi_dosha,
        "bhakoot_dosha": bhakoot_dosha
    }
