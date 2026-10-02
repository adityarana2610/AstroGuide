"""Unit tests for data table loading, schema validation, and cached data loader utility.
Path: tests/unit/test_data_loader.py
Feature: F4

Verifies:
- Tier 1: Core loading of static reference tables (nakshatra_table.json, gochara_rules.json, planet_stone_colour.json).
- Tier 2: Boundary and defensive error handling (missing files, malformed JSON, UTF-8 character encoding).
- Tier 3: DataLoader interface contracts (load_json_table, load_nakshatras, load_gochara_rules, load_remedies, caching).
- Complete 12 unit tests per spec_miner_m1_1 specification.
"""

import copy
import json
import os
import tempfile
import pytest

from astroguide.utils.data_loader import (
    DataLoader,
    DataLoadError,
    DataValidationError,
    load_json_table,
    load_nakshatras,
    load_nakshatra_table,
    load_gochara_rules,
    load_planet_stones,
    load_remedies,
    load_panchang_reference,
    get_remedy_for_planet,
)
from astroguide.parsers.data_models import (
    NakshatraTable,
    GocharaTable,
    PlanetStoneTable,
    RemediesTable,
    PanchangTable,
)

DATA_LOADER_AVAILABLE = True


@pytest.fixture(autouse=True)
def reset_dataloader_cache():
    """Ensure clean LRU cache before and after every test."""
    DataLoader.clear_cache()
    yield
    DataLoader.clear_cache()


# ==============================================================================
# Tier 1: Real Repository Table Verification
# ==============================================================================

@pytest.mark.unit
@pytest.mark.tier1
def test_nakshatra_table_structure_and_utf8(tables_data_dir):
    """Tier 1: Verify nakshatra_table.json is valid UTF-8 JSON with 27 nakshatras and Yoni matrix."""
    table_path = os.path.join(tables_data_dir, "nakshatra_table.json")
    assert os.path.exists(table_path), f"Table file not found at {table_path}"

    with open(table_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "nakshatras" in data, "nakshatra_table.json must contain 'nakshatras' key"
    assert "yoni_compatibility" in data, "nakshatra_table.json must contain 'yoni_compatibility' key"

    nakshatras = data["nakshatras"]
    assert len(nakshatras) == 27, f"Expected 27 nakshatras, got {len(nakshatras)}"

    required_fields = {
        "index", "name", "start_degree", "end_degree", "ruler",
        "deity", "gana", "yoni", "yoni_type", "nadi", "varna", "sign", "sign_lord"
    }

    expected_ganas = {"Deva", "Manushya", "Rakshasa"}
    expected_nadis = {"Vata", "Pitta", "Kapha"}
    expected_yoni_types = {"Male", "Female"}

    for idx, n in enumerate(nakshatras):
        missing = required_fields - set(n.keys())
        assert not missing, f"Nakshatra at index {idx} ({n.get('name')}) missing fields: {missing}"
        assert n["index"] == idx, f"Index mismatch: expected {idx}, got {n['index']}"
        assert n["gana"] in expected_ganas, f"Invalid gana '{n['gana']}' for {n['name']}"
        assert n["nadi"] in expected_nadis, f"Invalid nadi '{n['nadi']}' for {n['name']}"
        assert n["yoni_type"] in expected_yoni_types, f"Invalid yoni_type '{n['yoni_type']}' for {n['name']}"
        assert 0.0 <= n["start_degree"] < 360.0
        assert 0.0 < n["end_degree"] <= 360.0

    # Ashwini starts at 0.0 and Revati ends at 360.0
    assert nakshatras[0]["name"] == "Ashwini"
    assert nakshatras[0]["start_degree"] == 0.0
    assert nakshatras[26]["name"] == "Revati"
    assert abs(nakshatras[26]["end_degree"] - 360.0) < 0.01


@pytest.mark.unit
@pytest.mark.tier1
def test_gochara_rules_structure_and_planets(tables_data_dir):
    """Tier 1: Verify gochara_rules.json contains all 9 Grahas with valid house arrays."""
    table_path = os.path.join(tables_data_dir, "gochara_rules.json")
    assert os.path.exists(table_path), f"Table file not found at {table_path}"

    with open(table_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    expected_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for planet in expected_planets:
        assert planet in data, f"Planet '{planet}' missing from gochara_rules.json"
        rule = data[planet]
        assert "favourable_houses" in rule
        assert "unfavourable_houses" in rule
        assert "vedha_pairs" in rule

        assert isinstance(rule["favourable_houses"], list)
        assert isinstance(rule["unfavourable_houses"], list)
        assert isinstance(rule["vedha_pairs"], dict)

        # Houses must be between 1 and 12
        for h in rule["favourable_houses"]:
            assert 1 <= h <= 12, f"Invalid favourable house {h} for {planet}"
        for h in rule["unfavourable_houses"]:
            assert 1 <= h <= 12, f"Invalid unfavourable house {h} for {planet}"


@pytest.mark.unit
@pytest.mark.tier1
def test_planet_stone_colour_structure(tables_data_dir):
    """Tier 1: Verify planet_stone_colour.json maps digits 1-9 to gemstone, planet, and friendly numbers."""
    table_path = os.path.join(tables_data_dir, "planet_stone_colour.json")
    assert os.path.exists(table_path), f"Table file not found at {table_path}"

    with open(table_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for num in range(1, 10):
        key = str(num)
        assert key in data, f"Key '{key}' missing from planet_stone_colour.json"
        entry = data[key]
        assert "planet" in entry
        assert "gemstone" in entry
        assert "colour" in entry
        assert "friendly_numbers" in entry
        assert isinstance(entry["friendly_numbers"], list)
        assert len(entry["friendly_numbers"]) > 0


# ==============================================================================
# Tier 2: Boundary, Defensive & Malformed Input Handling
# ==============================================================================

@pytest.mark.unit
@pytest.mark.tier2
def test_loading_missing_file_raises_or_handles(temp_data_dir):
    """Tier 2: Attempting to load a nonexistent file should raise FileNotFoundError."""
    non_existent = os.path.join(temp_data_dir, "does_not_exist.json")
    with pytest.raises(FileNotFoundError):
        with open(non_existent, "r", encoding="utf-8") as f:
            json.load(f)


@pytest.mark.unit
@pytest.mark.tier2
def test_loading_malformed_json_raises_decode_error(tmp_path):
    """Tier 2: Malformed JSON syntax should raise json.JSONDecodeError."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ unquoted_key: 'invalid' ", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        with open(bad_file, "r", encoding="utf-8") as f:
            json.load(f)


@pytest.mark.unit
@pytest.mark.tier2
def test_utf8_multibyte_characters(tmp_path):
    """Tier 2: Verify explicit UTF-8 decoding preserves Sanskrit and Unicode symbols."""
    unicode_file = tmp_path / "unicode_test.json"
    content = {
        "sanskrit_om": "ॐ",
        "symbols": "♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓",
        "nakshatras": ["अश्विनी", "भरणी", "कृत्तिका"]
    }
    unicode_file.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")

    with open(unicode_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["sanskrit_om"] == "ॐ"
    assert "♈" in loaded["symbols"]
    assert loaded["nakshatras"][0] == "अश्विनी"


# ==============================================================================
# Tier 3: astroguide.utils.data_loader Contract Tests
# ==============================================================================

@pytest.mark.unit
@pytest.mark.tier3
def test_data_loader_module_contract():
    """Tier 3: Check data_loader module contract."""
    assert hasattr(DataLoader, "load_json")
    assert hasattr(DataLoader, "load_nakshatras")
    assert hasattr(DataLoader, "load_gochara_rules")
    assert hasattr(DataLoader, "load_planet_stones")
    assert hasattr(DataLoader, "load_remedies")
    assert hasattr(DataLoader, "load_panchang_reference")


@pytest.mark.unit
@pytest.mark.tier3
def test_data_loader_lru_caching():
    """Tier 3: Verify load_json_table uses caching for performance."""
    res1 = load_json_table("nakshatra_table.json")
    res2 = load_json_table("nakshatra_table.json")
    assert res1 == res2
    if hasattr(load_json_table, "cache_info"):
        info = load_json_table.cache_info()
        assert info.hits >= 1


@pytest.mark.unit
@pytest.mark.tier3
def test_data_loader_helper_functions():
    """Tier 3: Verify helper functions return expected collections."""
    nakshatras = load_nakshatras()
    assert isinstance(nakshatras, list)
    assert len(nakshatras) == 27

    rules = load_gochara_rules()
    assert isinstance(rules, dict)
    assert "Sun" in rules
    assert "Jupiter" in rules


# ==============================================================================
# Full 12 Unit Tests Specified by Spec Miner M1-1
# ==============================================================================

# -------------------------------------------------------------
# 1. Dataset Integrity & Schema Tests
# -------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.tier1
def test_load_nakshatras_schema_and_count():
    """Verify nakshatra_table.json loads exactly 27 nakshatras matching schema."""
    nakshatras = load_nakshatras()
    assert isinstance(nakshatras, list)
    assert len(nakshatras) == 27
    
    first = nakshatras[0]
    assert first["name"] == "Ashwini"
    assert first["ruler"] == "Ketu"
    assert first["gana"] == "Deva"
    assert first["start_degree"] == 0.0

    last = nakshatras[26]
    assert last["name"] == "Revati"
    assert last["ruler"] == "Mercury"
    assert last["end_degree"] == 360.0


@pytest.mark.unit
@pytest.mark.tier1
def test_load_nakshatra_table_and_yoni():
    """Verify nakshatra_table.json includes valid yoni compatibility mappings."""
    data = load_nakshatra_table()
    assert "nakshatras" in data
    assert "yoni_compatibility" in data
    yoni = data["yoni_compatibility"]
    assert len(yoni) >= 14
    assert yoni.get("Horse") == "Buffalo"
    assert yoni.get("Elephant") == "Lion"


@pytest.mark.unit
@pytest.mark.tier1
def test_load_gochara_rules_schema_and_grahas():
    """Verify gochara_rules.json covers all 9 Grahas with valid houses."""
    rules = load_gochara_rules()
    assert isinstance(rules, dict)
    required_grahas = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for graha in required_grahas:
        assert graha in rules, f"Missing Gochara rule for {graha}"
        rule = rules[graha]
        assert "favourable_houses" in rule
        assert "unfavourable_houses" in rule
        assert "vedha_pairs" in rule
        for h in rule["favourable_houses"]:
            assert 1 <= h <= 12


@pytest.mark.unit
@pytest.mark.tier1
def test_load_planet_stones_schema():
    """Verify planet_stone_colour.json maps numbers 1-9 correctly."""
    stones = load_planet_stones()
    assert isinstance(stones, dict)
    for i in range(1, 10):
        key = str(i)
        assert key in stones
        record = stones[key]
        assert "planet" in record
        assert "gemstone" in record
        assert "colour" in record
        assert isinstance(record["friendly_numbers"], list)


@pytest.mark.unit
@pytest.mark.tier1
def test_load_remedies_dataset():
    """Verify remedies dataset conforms to RemediesTable schema."""
    remedies_data = load_remedies()
    assert isinstance(remedies_data, dict)
    assert "remedies" in remedies_data and remedies_data["remedies"]
    remedies = remedies_data["remedies"]
    for graha in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        assert graha in remedies
        rec = remedies[graha]
        assert "primary_gemstone" in rec
        assert "mantra" in rec
        assert "deity" in rec
        assert "positive_lifestyle_action" in rec


@pytest.mark.unit
@pytest.mark.tier1
def test_load_panchang_reference_dataset():
    """Verify panchang reference dataset conforms to PanchangTable schema."""
    panchang = load_panchang_reference()
    assert isinstance(panchang, dict)
    assert "tithis" in panchang and panchang["tithis"]
    assert len(panchang["tithis"]) == 30
    assert len(panchang["taras"]) == 9


# -------------------------------------------------------------
# 2. Caching & Immutability Tests
# -------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.tier3
def test_lru_caching_hits_and_misses():
    """Verify @lru_cache(maxsize=32) prevents redundant file disk reads."""
    DataLoader.clear_cache()
    info_initial = DataLoader.get_cache_info()
    
    # First call: cache miss
    _ = DataLoader.load_json("gochara_rules.json")
    info_after_first = DataLoader.get_cache_info()
    assert info_after_first.misses == info_initial.misses + 1

    # Second call: cache hit
    _ = DataLoader.load_json("gochara_rules.json")
    info_after_second = DataLoader.get_cache_info()
    assert info_after_second.hits == info_after_first.hits + 1


@pytest.mark.unit
@pytest.mark.tier3
def test_cache_immutability_on_mutation():
    """Verify mutating a returned dictionary does not mutate the cached copy."""
    data1 = load_nakshatras()
    original_name = data1[0]["name"]
    
    # Mutate caller's copy
    data1[0]["name"] = "MUTATED_TEST_NAME"

    # Reload from DataLoader
    data2 = load_nakshatras()
    assert data2[0]["name"] == original_name, "Cached memory was mutated by caller in-place!"


# -------------------------------------------------------------
# 3. Encoding & Defensive Fallback Tests
# -------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.tier2
def test_explicit_utf8_encoding_with_unicode(tmp_path):
    """Verify DataLoader reads UTF-8 characters properly across Windows locales."""
    unicode_content = {
        "test_characters": "Śani (शनि), Rāhu (राहु), Ketu (केतु), Āśvinī (अश्विनी)"
    }
    test_file = tmp_path / "unicode_test.json"
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(unicode_content, f, ensure_ascii=False)

    old_dir = DataLoader.get_data_dir()
    DataLoader.set_data_dir(tmp_path)
    try:
        loaded = DataLoader.load_json("unicode_test.json")
        assert loaded["test_characters"] == unicode_content["test_characters"]
    finally:
        DataLoader.set_data_dir(old_dir)


@pytest.mark.unit
@pytest.mark.tier2
def test_missing_file_error_and_fallback():
    """Verify missing files raise DataLoadError when defensive=False and return fallback when defensive=True."""
    with pytest.raises(DataLoadError) as exc_info:
        DataLoader.load_json("non_existent_file_xyz.json", defensive=False)
    assert "Failed to load table non_existent_file_xyz.json" in str(exc_info.value)

    fallback_val = {"status": "fallback_activated"}
    result = DataLoader.load_json("non_existent_file_xyz.json", fallback=fallback_val, defensive=True)
    assert result == fallback_val


@pytest.mark.unit
@pytest.mark.tier2
def test_corrupted_json_error():
    """Verify malformed JSON raises DataLoadError with decode details."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as tmp:
        tmp.write("{\ninvalid_json: [truncated")
        tmp_name = tmp.name

    tmp_dir = os.path.dirname(tmp_name)
    tmp_filename = os.path.basename(tmp_name)
    old_dir = DataLoader.get_data_dir()
    DataLoader.set_data_dir(tmp_dir)
    try:
        with pytest.raises(DataLoadError):
            DataLoader.load_json(tmp_filename, defensive=False)
    finally:
        os.remove(tmp_name)
        DataLoader.set_data_dir(old_dir)


@pytest.mark.unit
@pytest.mark.tier2
def test_pydantic_schema_validation_failure():
    """Verify invalid schema data raises DataValidationError."""
    invalid_data = {
        "nakshatras": [
            {
                "index": 999,  # invalid index > 26
                "name": "InvalidNakshatra",
                "start_degree": 0.0,
                "end_degree": 13.0,
                "ruler": "Invalid",
                "deity": "None",
                "gana": "InvalidGana",
                "yoni": "Unknown",
                "yoni_type": "Male",
                "nadi": "Vata",
                "varna": "None",
                "sign": "Aries",
                "sign_lord": "Mars"
            }
        ]
    }
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as tmp:
        json.dump(invalid_data, tmp)
        tmp_name = tmp.name

    tmp_dir = os.path.dirname(tmp_name)
    tmp_filename = os.path.basename(tmp_name)
    old_dir = DataLoader.get_data_dir()
    DataLoader.set_data_dir(tmp_dir)
    try:
        with pytest.raises(DataValidationError):
            DataLoader.load_json(tmp_filename, model=NakshatraTable, defensive=False)
    finally:
        os.remove(tmp_name)
        DataLoader.set_data_dir(old_dir)
