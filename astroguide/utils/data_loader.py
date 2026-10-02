"""
Centralized, Cached Data Loader with Schema Validation and Defensive Fallback.
Module: astroguide.utils.data_loader
Feature: F4
"""
import copy
import functools
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, ValidationError

# Import validation schemas
from astroguide.parsers.data_models import (
    GocharaTable,
    NakshatraRecord,
    NakshatraTable,
    PanchangTable,
    PlanetStoneTable,
    RemediesTable,
    RemedyRecord,
    TaraRecord,
    TithiRecord,
)

logger = logging.getLogger(__name__)

# Default directory for static JSON tables: <project_root>/data/tables
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "tables"


class DataLoadError(Exception):
    """Raised when a data table file cannot be found or read."""
    pass


class DataValidationError(Exception):
    """Raised when a loaded dataset fails Pydantic schema validation."""
    pass


@functools.lru_cache(maxsize=32)
def _read_raw_json_cached(filepath_str: str) -> Any:
    """
    Internal LRU-cached reader with explicit UTF-8 encoding.
    Caches parsed JSON based on the canonical file path string.
    """
    path = Path(filepath_str)
    if not path.is_file():
        raise FileNotFoundError(f"Data table file does not exist: {filepath_str}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class DataLoader:
    """
    Centralized loader for AstroGuide static reference tables.
    Features:
      1. @functools.lru_cache(maxsize=32) avoids redundant file reads.
      2. Explicit encoding="utf-8" prevents Windows locale decode bugs.
      3. Deep copy on retrieval prevents callers from mutating cached memory.
      4. Pydantic schema validation validates data integrity on load.
      5. Configurable defensive fallbacks for missing or corrupt files.
    """
    _data_dir: Path = DEFAULT_DATA_DIR

    @classmethod
    def set_data_dir(cls, custom_dir: Union[str, Path]) -> None:
        """Sets a custom directory for table files and invalidates current cache."""
        cls._data_dir = Path(custom_dir).resolve()
        cls.clear_cache()

    @classmethod
    def get_data_dir(cls) -> Path:
        """Returns the active data directory."""
        return cls._data_dir

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the underlying LRU cache."""
        _read_raw_json_cached.cache_clear()

    @classmethod
    def get_cache_info(cls):
        """Returns LRU cache statistics (hits, misses, maxsize, currsize)."""
        return _read_raw_json_cached.cache_info()

    @classmethod
    def load_json(
        cls,
        filename: str,
        model: Optional[Type[BaseModel]] = None,
        fallback: Optional[Any] = None,
        defensive: bool = False
    ) -> Any:
        """
        Loads a JSON table by filename from data/tables/.
        """
        filepath = cls._data_dir / filename
        filepath_str = str(filepath.resolve())

        try:
            raw_data = _read_raw_json_cached(filepath_str)
            # Return deepcopy to ensure mutations do not pollute cached instances
            data_copy = copy.deepcopy(raw_data)

            if model is not None:
                try:
                    validated_model = model.model_validate(data_copy)
                    return validated_model
                except ValidationError as ve:
                    logger.error(f"Schema validation error in {filename}: {ve}")
                    if defensive and fallback is not None:
                        return fallback
                    raise DataValidationError(f"Schema validation failed for {filename}: {ve}") from ve

            return data_copy

        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load table {filename} from {filepath_str}: {e}")
            if defensive and fallback is not None:
                return fallback
            raise DataLoadError(f"Failed to load table {filename} from {filepath_str}: {e}") from e

    # -------------------------------------------------------------
    # Strongly-typed helper methods for core datasets
    # -------------------------------------------------------------

    @classmethod
    def load_nakshatras(cls, validate: bool = True, defensive: bool = False) -> List[Dict[str, Any]]:
        """Returns the list of 27 Nakshatra dictionaries."""
        model = NakshatraTable if validate else None
        data = cls.load_json("nakshatra_table.json", model=model, fallback={}, defensive=defensive)
        if isinstance(data, NakshatraTable):
            return [n.model_dump() for n in data.nakshatras]
        return data.get("nakshatras", [])

    @classmethod
    def load_nakshatra_table(cls, validate: bool = True, defensive: bool = False) -> Dict[str, Any]:
        """Returns the complete Nakshatra table dict with nakshatras and yoni_compatibility."""
        model = NakshatraTable if validate else None
        data = cls.load_json("nakshatra_table.json", model=model, fallback={}, defensive=defensive)
        if isinstance(data, NakshatraTable):
            return data.model_dump()
        return data

    @classmethod
    def load_gochara_rules(cls, validate: bool = True, defensive: bool = False) -> Dict[str, Any]:
        """Returns Gochara transit rules and Vedha pairs for all 9 Grahas."""
        model = GocharaTable if validate else None
        data = cls.load_json("gochara_rules.json", model=model, fallback={}, defensive=defensive)
        if isinstance(data, GocharaTable):
            return data.model_dump()
        return data

    @classmethod
    def load_planet_stones(cls, validate: bool = True, defensive: bool = False) -> Dict[str, Any]:
        """Returns planet-gemstone-colour mappings for numbers 1 to 9."""
        model = PlanetStoneTable if validate else None
        data = cls.load_json("planet_stone_colour.json", model=model, fallback={}, defensive=defensive)
        if isinstance(data, PlanetStoneTable):
            return data.model_dump()
        return data

    @classmethod
    def load_remedies(cls, validate: bool = True, defensive: bool = True) -> Dict[str, Any]:
        """Returns astrological remedies for all 9 Grahas (Feature F1)."""
        model = RemediesTable if validate else None
        data = cls.load_json("astrological_remedies.json", model=model, fallback={"remedies": {}}, defensive=defensive)
        if isinstance(data, RemediesTable):
            return data.model_dump()
        return data

    @classmethod
    def load_panchang_reference(cls, validate: bool = True, defensive: bool = True) -> Dict[str, Any]:
        """Returns panchang reference data covering Tithis, Taras, and Muhurtha actions (Feature F2)."""
        model = PanchangTable if validate else None
        data = cls.load_json("panchang_reference.json", model=model, fallback={}, defensive=defensive)
        if isinstance(data, PanchangTable):
            return data.model_dump()
        return data


# =====================================================================
# Standalone Module Functions (matching PROJECT.md Interface Contracts)
# =====================================================================

def load_json_table(filename: str) -> dict:
    """Loads a JSON file from data/tables/ with LRU caching and explicit UTF-8."""
    return DataLoader.load_json(filename)

load_json_table.cache_info = DataLoader.get_cache_info
load_json_table.cache_clear = DataLoader.clear_cache

def load_remedies() -> dict:
    """Returns astrological remedies for all 9 Grahas."""
    return DataLoader.load_remedies()

def get_remedy_for_planet(planet_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves the remedy record for a given planet (case-insensitive)."""
    remedies_dict = DataLoader.load_remedies()
    remedies = remedies_dict.get("remedies", remedies_dict)
    normalized = planet_name.strip().capitalize()
    return remedies.get(normalized)

def load_nakshatras() -> list:
    """Returns list of 27 nakshatra dictionaries."""
    return DataLoader.load_nakshatras()

def load_nakshatra_table() -> dict:
    """Returns the complete nakshatra table dictionary."""
    return DataLoader.load_nakshatra_table()

def load_gochara_rules() -> dict:
    """Returns Gochara transit rules and Vedha pairs."""
    return DataLoader.load_gochara_rules()

def load_planet_stones() -> dict:
    """Returns numerological planet-gemstone-colour mappings."""
    return DataLoader.load_planet_stones()

load_planet_stone_colour = load_planet_stones

def load_panchang_reference() -> dict:
    """Returns panchang reference data."""
    return DataLoader.load_panchang_reference()
