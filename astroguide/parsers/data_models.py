"""
Pydantic Data Models for Astrology Datasets and Calculation Tables.
Module: astroguide.parsers.data_models
Feature: F4
"""
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, RootModel, field_validator


# ==========================================
# 1. Nakshatra Table Models
# ==========================================

class NakshatraRecord(BaseModel):
    """Validation schema for an individual Nakshatra record (0 to 26)."""
    index: int = Field(..., ge=0, le=26, description="0-based index from Ashwini (0) to Revati (26)")
    name: str = Field(..., min_length=2, description="Nakshatra name in English / IAST")
    start_degree: float = Field(..., ge=0.0, lt=360.0, description="Starting sidereal degree in zodiac")
    end_degree: float = Field(..., gt=0.0, le=360.0, description="Ending sidereal degree in zodiac")
    ruler: str = Field(..., description="Vimshottari planetary ruler")
    deity: str = Field(..., description="Presiding Vedic deity")
    gana: Literal["Deva", "Manushya", "Rakshasa"] = Field(..., description="Temperament / Gana")
    yoni: str = Field(..., min_length=2, description="Animal totem for sexual / instinctual compatibility")
    yoni_type: Literal["Male", "Female"] = Field(..., description="Animal gender")
    nadi: Literal["Vata", "Pitta", "Kapha"] = Field(..., description="Ayurvedic constitution / Nadi")
    varna: str = Field(..., description="Spiritual caste / temperament")
    sign: str = Field(..., description="Primary zodiac sign or signs spanned")
    sign_lord: str = Field(..., description="Ruling planet of primary zodiac sign")

    @field_validator("end_degree")
    @classmethod
    def validate_degree_span(cls, v: float, info: Any) -> float:
        start = info.data.get("start_degree")
        if start is not None and v <= start:
            raise ValueError(f"end_degree ({v}) must be greater than start_degree ({start})")
        return v


class NakshatraTable(BaseModel):
    """Validation schema for data/tables/nakshatra_table.json."""
    nakshatras: List[NakshatraRecord] = Field(..., description="List of 27 classical Nakshatras")
    yoni_compatibility: Dict[str, str] = Field(
        default_factory=dict, 
        description="Map of animal totems to their mortal enemies"
    )

    @field_validator("nakshatras")
    @classmethod
    def validate_nakshatra_count(cls, v: List[NakshatraRecord]) -> List[NakshatraRecord]:
        if len(v) != 27:
            raise ValueError(f"Nakshatra table must contain exactly 27 nakshatras, found {len(v)}")
        indices = [n.index for n in v]
        if indices != list(range(27)):
            raise ValueError("Nakshatras must be indexed sequentially from 0 to 26")
        return v


# ==========================================
# 2. Gochara Rules Models
# ==========================================

class GocharaPlanetRule(BaseModel):
    """Transit rules for an individual planet from the natal Moon."""
    favourable_houses: List[int] = Field(..., description="Houses where transit produces auspicious results")
    unfavourable_houses: List[int] = Field(..., description="Houses where transit produces challenges")
    vedha_pairs: Dict[str, int] = Field(
        default_factory=dict, 
        description="Obstruction map: favourable_house -> blocking_house"
    )

    @field_validator("favourable_houses", "unfavourable_houses")
    @classmethod
    def validate_houses(cls, v: List[int]) -> List[int]:
        for h in v:
            if not (1 <= h <= 12):
                raise ValueError(f"House number must be between 1 and 12, got {h}")
        return v


class GocharaTable(RootModel[Dict[str, GocharaPlanetRule]]):
    """Validation schema for data/tables/gochara_rules.json (9 Grahas)."""
    pass


# ==========================================
# 3. Astrological Remedies Models (Feature F1)
# ==========================================

class VedicMantras(BaseModel):
    """Vedic Beej, Nama, and Gayatri mantras with recitation count."""
    beej_mantra: str = Field(...)
    nama_mantra: Optional[str] = None
    gayatri_mantra: Optional[str] = None
    recitation_count: Optional[int] = None


class RudrakshaDetails(BaseModel):
    """Detailed Rudraksha bead attributes."""
    mukhi: str = Field(...)
    ruling_planet: Optional[str] = None
    significance: Optional[str] = None


class RemedyRecord(BaseModel):
    """Comprehensive remedial guidance for a single Graha."""
    planet: str = Field(..., description="Planet name (Sun, Moon, Mars, etc.)")
    sanskrit_name: Optional[str] = None
    vedic_number: Optional[int] = None
    primary_gemstone: str = Field(..., description="Prescribed primary Jyotish gemstone")
    substitute_gemstone: Optional[str] = Field(default=None, description="Accessible semi-precious alternative")
    substitute_gemstones: List[str] = Field(default_factory=list)
    metal: str = Field(..., description="Recommended setting metal (Gold, Silver, Copper, etc.)")
    wear_finger: str = Field(..., description="Prescribed hand finger (Ring, Middle, Little, Index)")
    wear_day: str = Field(..., description="Auspicious day and tithi timing to wear gemstone")
    wear_time: Optional[str] = None
    weight_carats: Optional[str] = None
    mantra: str = Field(..., description="Vedic or Beej mantra with repetition guidelines")
    vedic_mantras: Optional[Union[VedicMantras, Dict[str, Any]]] = None
    deity: str = Field(..., description="Presiding divine archetype for meditation and prayer")
    deities: List[str] = Field(default_factory=list)
    rudraksha: str = Field(..., description="Recommended Rudraksha bead mukhi count")
    rudraksha_details: Optional[Union[RudrakshaDetails, Dict[str, Any]]] = None
    charity_items: List[str] = Field(default_factory=list, description="Items to donate for pacification")
    charity_recipients: Optional[str] = None
    fasting_day: str = Field(..., description="Prescribed day of week for fasting or light diet")
    fasting_rules: Optional[str] = None
    positive_lifestyle_action: str = Field(
        ..., 
        description="Constructive psychological and behavioural habit to harmonize planetary energy"
    )
    positive_lifestyle_actions: List[str] = Field(default_factory=list)


# Alias for compatibility with explorer_m1_1 naming
PlanetRemedyRecord = RemedyRecord


class RemediesTable(BaseModel):
    """Validation schema for data/tables/astrological_remedies.json."""
    metadata: Optional[Dict[str, Any]] = None
    remedies: Dict[str, RemedyRecord] = Field(..., description="Remedies keyed by Graha name")

    @field_validator("remedies")
    @classmethod
    def validate_all_grahas(cls, v: Dict[str, RemedyRecord]) -> Dict[str, RemedyRecord]:
        required_grahas = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        missing = required_grahas - set(v.keys())
        if missing:
            raise ValueError(f"Remedies table missing required Grahas: {missing}")
        return v


# Alias for compatibility with explorer_m1_1 naming
AstrologicalRemediesDataset = RemediesTable


# ==========================================
# 4. Panchang Reference Models (Feature F2)
# ==========================================

class TithiRecord(BaseModel):
    """Specification for a single lunar day (Tithi)."""
    number: int = Field(..., ge=1, le=30, description="Tithi number 1-30 (1-15 Shukla, 16-30 Krishna)")
    name: str = Field(..., description="Sanskrit name of Tithi")
    paksha: Literal["Shukla", "Krishna"] = Field(..., description="Lunar fortnight")
    category: str = Field(..., description="Nanda, Bhadra, Jaya, Rikta, or Poorna")
    category_ruler: Optional[str] = None
    deity: Optional[str] = None
    is_shubh: bool = Field(..., description="Whether universally auspicious for general muhurtha")
    score: int = Field(default=0, description="Standard scoring weight (-2 to +2)")
    auspicious_activities: List[str] = Field(default_factory=list)
    inauspicious_activities: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class TaraRecord(BaseModel):
    """Specification for a Tarabala category (1 of 9)."""
    number: int = Field(..., ge=1, le=9, description="Tara cycle position 1 to 9")
    name: str = Field(..., description="Janma, Sampat, Vipat, Kshema, Pratyari, Sadhaka, Vadha, Mitra, Ati-Mitra")
    sanskrit_name: Optional[str] = None
    english_meaning: Optional[str] = None
    score: int = Field(..., description="Score weight (-1, 0, or 1)")
    is_favourable: bool = Field(...)
    description: Optional[str] = None
    recommended_actions: List[str] = Field(default_factory=list)
    avoid_actions: List[str] = Field(default_factory=list)


class PanchangTable(BaseModel):
    """Validation schema for data/tables/panchang_reference.json."""
    metadata: Optional[Dict[str, Any]] = None
    tithis: List[TithiRecord] = Field(..., description="List of 30 Tithis")
    taras: List[TaraRecord] = Field(..., description="List of 9 Taras")
    muhurtha_actions: Optional[Dict[str, Any]] = None
    karanas: Optional[List[Dict[str, Any]]] = None
    nitya_yogas: Optional[List[Dict[str, Any]]] = None

    @field_validator("tithis")
    @classmethod
    def validate_tithi_count(cls, v: List[TithiRecord]) -> List[TithiRecord]:
        if len(v) != 30:
            raise ValueError(f"Panchang table must contain exactly 30 tithis, found {len(v)}")
        return v

    @field_validator("taras")
    @classmethod
    def validate_tara_count(cls, v: List[TaraRecord]) -> List[TaraRecord]:
        if len(v) != 9:
            raise ValueError(f"Panchang table must contain exactly 9 taras, found {len(v)}")
        return v


# ==========================================
# 5. Numerology / Planet Stone Models
# ==========================================

class PlanetStoneRecord(BaseModel):
    """Numerological mapping for numbers 1 to 9."""
    planet: str = Field(...)
    gemstone: str = Field(...)
    colour: str = Field(...)
    friendly_planets: List[str] = Field(default_factory=list)
    unfriendly_planets: List[str] = Field(default_factory=list)
    friendly_numbers: List[int] = Field(default_factory=list)


class PlanetStoneTable(RootModel[Dict[str, PlanetStoneRecord]]):
    """Validation schema for data/tables/planet_stone_colour.json."""
    pass
