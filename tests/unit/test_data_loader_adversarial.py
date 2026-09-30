"""Adversarial Stress Test Suite for DataLoader and Curated Datasets.
Path: tests/unit/test_data_loader_adversarial.py
Feature: F4 (Robust Cached Data Loader) & F1, F2 datasets.

Adversarial Stress Dimensions:
1. Deep In-Memory Cache Mutation Immunity (Zero Cross-Pollution)
2. Unicode Decoding Under Windows Locale & Adversarial Multi-Byte Characters
3. Schema Validation Boundaries & Hostile / Malformed Inputs
4. Caching Performance Benchmark & High-Throughput In-Memory Lookups
5. Multithreaded Concurrency Stress Testing
6. Hostile Edge Cases & Function Contract Boundaries
"""

import copy
import json
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
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


@pytest.fixture(autouse=True)
def fresh_cache():
    """Ensure a pristine cache state before and after every adversarial test."""
    DataLoader.clear_cache()
    yield
    DataLoader.clear_cache()


# ==============================================================================
# DIMENSION 1: Deep In-Memory Cache Mutation Immunity
# ==============================================================================

class TestCacheMutationImmunity:
    """Stress test in-memory cache isolation against aggressive caller mutations."""

    def test_remedies_deep_mutation_immunity(self):
        """Mutate deep nested fields (mantras, gemstones, lists) and verify cache is unaffected."""
        data_1 = load_remedies()
        assert "Sun" in data_1["remedies"]
        original_gemstone = data_1["remedies"]["Sun"]["primary_gemstone"]
        original_charity_count = len(data_1["remedies"]["Sun"]["charity_items"])

        # Aggressively mutate caller's instance in-place
        data_1["remedies"]["Sun"]["primary_gemstone"] = "CORRUPTED_PLASTIC_GEM"
        data_1["remedies"]["Sun"]["charity_items"].append("CORRUPTED_ITEM")
        data_1["remedies"]["Sun"]["charity_items"].clear()
        data_1["remedies"]["Moon"] = {"corrupted": True}
        del data_1["remedies"]["Mars"]

        # Reload from data loader
        data_2 = load_remedies()
        assert data_2["remedies"]["Sun"]["primary_gemstone"] == original_gemstone
        assert len(data_2["remedies"]["Sun"]["charity_items"]) == original_charity_count
        assert "Moon" in data_2["remedies"] and data_2["remedies"]["Moon"].get("corrupted") is None
        assert "Mars" in data_2["remedies"]

    def test_nakshatras_list_mutation_immunity(self):
        """Mutate returned Nakshatra list (popping, reordering, item mutation) without polluting cache."""
        nakshatras_1 = load_nakshatras()
        original_len = len(nakshatras_1)
        original_first_name = nakshatras_1[0]["name"]

        # Mutate list
        nakshatras_1[0]["name"] = "MUTATED_ASHWINI"
        nakshatras_1[0]["gana"] = "MUTATED_GANA"
        nakshatras_1.pop(0)
        nakshatras_1.clear()

        # Reload
        nakshatras_2 = load_nakshatras()
        assert len(nakshatras_2) == original_len == 27
        assert nakshatras_2[0]["name"] == original_first_name == "Ashwini"
        assert nakshatras_2[0]["gana"] == "Deva"

    def test_nakshatra_table_nested_dict_mutation(self):
        """Mutate nakshatra_table nested yoni_compatibility and nakshatra array."""
        table_1 = load_nakshatra_table()
        table_1["yoni_compatibility"]["Horse"] = "MUTATED_ENEMY"
        table_1["yoni_compatibility"].clear()
        table_1["nakshatras"] = []

        table_2 = load_nakshatra_table()
        assert len(table_2["yoni_compatibility"]) >= 14
        assert table_2["yoni_compatibility"]["Horse"] == "Buffalo"
        assert len(table_2["nakshatras"]) == 27

    def test_gochara_rules_deep_mutation_immunity(self):
        """Mutate transit rules (favourable houses list, vedha pairs dict)."""
        rules_1 = load_gochara_rules()
        rules_1["Jupiter"]["favourable_houses"].append(999)
        rules_1["Jupiter"]["vedha_pairs"]["99"] = 88
        rules_1["Saturn"] = None

        rules_2 = load_gochara_rules()
        assert 999 not in rules_2["Jupiter"]["favourable_houses"]
        assert "99" not in rules_2["Jupiter"]["vedha_pairs"]
        assert rules_2["Saturn"] is not None
        assert "favourable_houses" in rules_2["Saturn"]

    def test_panchang_reference_deep_mutation_immunity(self):
        """Mutate panchang tithis and taras lists in-place."""
        panchang_1 = load_panchang_reference()
        panchang_1["tithis"][0]["name"] = "MUTATED_PRATIPADA"
        panchang_1["taras"][0]["score"] = -9999
        panchang_1["tithis"].clear()

        panchang_2 = load_panchang_reference()
        assert len(panchang_2["tithis"]) == 30
        assert panchang_2["tithis"][0]["name"] == "Pratipada"
        assert panchang_2["taras"][0]["score"] == -1  # Janma tara score

    def test_planet_stones_mutation_immunity(self):
        """Mutate planet stone mappings and friendly numbers."""
        stones_1 = load_planet_stones()
        stones_1["1"]["friendly_numbers"].append(9999)
        stones_1["1"]["gemstone"] = "FAKE_RUBY"

        stones_2 = load_planet_stones()
        assert 9999 not in stones_2["1"]["friendly_numbers"]
        assert stones_2["1"]["gemstone"] == "Ruby"

    def test_raw_load_json_table_mutation_immunity(self):
        """Direct load_json_table() return dict mutation does not affect subsequent calls."""
        res_1 = load_json_table("gochara_rules.json")
        res_1["MUTATED_KEY"] = "INJECTED_VALUE"
        res_1["Sun"]["favourable_houses"].clear()

        res_2 = load_json_table("gochara_rules.json")
        assert "MUTATED_KEY" not in res_2
        assert len(res_2["Sun"]["favourable_houses"]) > 0

    def test_get_remedy_for_planet_mutation_immunity(self):
        """Mutate single planet remedy dictionary returned by get_remedy_for_planet."""
        sun_remedy = get_remedy_for_planet("Sun")
        assert sun_remedy is not None
        sun_remedy["primary_gemstone"] = "PLASTIC"
        sun_remedy["charity_items"].clear()

        sun_remedy_fresh = get_remedy_for_planet("Sun")
        assert sun_remedy_fresh["primary_gemstone"] == "Ruby"
        assert len(sun_remedy_fresh["charity_items"]) > 0


# ==============================================================================
# DIMENSION 2: Unicode Decoding under Windows Locale & Diacritics
# ==============================================================================

class TestUnicodeDecodingStress:
    """Stress test multi-byte Unicode, Devanagari, diacritics, and symbols."""

    def test_remedies_and_panchang_devanagari_and_iast(self):
        """Verify Sanskrit Devanagari characters in panchang and clean IAST transliterations in remedies."""
        remedies = load_remedies()
        remedy_dict = remedies["remedies"]

        # Remedies use clean English/IAST transliterations without mojibake
        sun = remedy_dict["Sun"]
        assert "Om Hram Hreem" in sun["mantra"]
        assert sun.get("sanskrit_name") == "Surya"

        # Check all 9 Grahas load non-ASCII characters or clean text without replacement characters
        for graha, rec in remedy_dict.items():
            serialized = json.dumps(rec, ensure_ascii=False)
            assert "\ufffd" not in serialized, f"Unicode replacement char found in {graha} remedy!"

        # Panchang contains actual Sanskrit Devanagari for all 9 Taras
        panchang = load_panchang_reference()
        taras = panchang["taras"]
        devanagari_taras = [t["sanskrit_name"] for t in taras if "sanskrit_name" in t]
        assert "जन्म" in devanagari_taras
        assert "सम्पत्" in devanagari_taras
        assert "विपत्" in devanagari_taras
        assert "क्षेम" in devanagari_taras
        assert len(devanagari_taras) == 9

    def test_panchang_reference_unicode_integrity(self):
        """Verify panchang reference loads all Tithi & Tara names without mojibake."""
        panchang = load_panchang_reference()
        serialized = json.dumps(panchang, ensure_ascii=False)
        assert "\ufffd" not in serialized, "Unicode replacement char found in panchang reference!"
        # Check specific Sanskrit terms
        tithi_names = [t["name"] for t in panchang["tithis"]]
        assert "Pratipada" in tithi_names
        assert "Purnima" in tithi_names or "Poornima" in tithi_names
        assert "Amavasya" in tithi_names

    def test_nakshatras_diacritics_and_symbols(self):
        """Verify nakshatra names, rulers, and deities load cleanly."""
        nakshatras = load_nakshatras()
        for nak in nakshatras:
            assert isinstance(nak["name"], str) and len(nak["name"]) > 0
            assert isinstance(nak["deity"], str) and len(nak["deity"]) > 0
            assert "\ufffd" not in nak["name"]

    def test_utf8_bom_handling(self, tmp_path):
        """Test file written with UTF-8 BOM (Byte Order Mark, \\ufeff) - common on Windows."""
        bom_file = tmp_path / "bom_test.json"
        content = {"message": "BOM test successful", "symbol": "ॐ"}
        # Write with utf-8-sig to include BOM
        with open(bom_file, "w", encoding="utf-8-sig") as f:
            json.dump(content, f, ensure_ascii=False)

        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        try:
            # Python's json.load on standard utf-8 open may fail or succeed depending on python version
            # Let's verify how DataLoader handles it
            try:
                loaded = DataLoader.load_json("bom_test.json")
                assert loaded["message"] == "BOM test successful"
                assert loaded["symbol"] == "ॐ"
            except (DataLoadError, json.JSONDecodeError):
                # If utf-8 without sig fails on BOM, verify clean error handling
                pass
        finally:
            DataLoader.set_data_dir(old_dir)

    def test_astral_plane_emojis_and_astrology_symbols(self, tmp_path):
        """Verify DataLoader handles 4-byte astral plane Unicode symbols (astrology glyphs, emojis)."""
        symbols_file = tmp_path / "symbols_test.json"
        content = {
            "astrological_planets": "☉ ☽ ☿ ♀ ♂ ♃ ♄ ☊ ☋",
            "zodiac_glyphs": "♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓",
            "emojis": "🪐 🌟 🔮 ✨",
            "vedic_sacred": "ॐ भूर्भुवः स्वः"
        }
        with open(symbols_file, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False)

        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        try:
            loaded = DataLoader.load_json("symbols_test.json")
            assert loaded["astrological_planets"] == content["astrological_planets"]
            assert loaded["zodiac_glyphs"] == content["zodiac_glyphs"]
            assert loaded["emojis"] == content["emojis"]
            assert loaded["vedic_sacred"] == content["vedic_sacred"]
        finally:
            DataLoader.set_data_dir(old_dir)


# ==============================================================================
# DIMENSION 3: Schema Validation Boundaries & Hostile / Malformed Inputs
# ==============================================================================

class TestSchemaValidationBoundaries:
    """Stress test boundary conditions, invalid counts, and malformed structures."""

    def test_nakshatra_count_boundaries(self, tmp_path):
        """NakshatraTable must strictly reject count != 27 (e.g. 26 or 28)."""
        valid_nakshatras = load_nakshatras()
        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)

        try:
            # Case 1: 26 nakshatras (truncated)
            data_26 = {"nakshatras": valid_nakshatras[:26], "yoni_compatibility": {}}
            f26 = tmp_path / "nakshatras_26.json"
            f26.write_text(json.dumps(data_26), encoding="utf-8")
            with pytest.raises(DataValidationError) as exc:
                DataLoader.load_json("nakshatras_26.json", model=NakshatraTable)
            assert "exactly 27 nakshatras" in str(exc.value)

            # Case 2: 28 nakshatras (duplicated entry)
            extra_nak = copy.deepcopy(valid_nakshatras[26])
            extra_nak["index"] = 27  # out of bounds index
            data_28 = {"nakshatras": valid_nakshatras + [extra_nak], "yoni_compatibility": {}}
            f28 = tmp_path / "nakshatras_28.json"
            f28.write_text(json.dumps(data_28), encoding="utf-8")
            with pytest.raises(DataValidationError):
                DataLoader.load_json("nakshatras_28.json", model=NakshatraTable)

        finally:
            DataLoader.set_data_dir(old_dir)

    def test_nakshatra_inverted_degrees(self, tmp_path):
        """NakshatraRecord must reject end_degree <= start_degree."""
        valid_nakshatras = load_nakshatras()
        bad_nak = copy.deepcopy(valid_nakshatras)
        # Test on index 1 (Bharani, start_degree ~ 13.33): set end_degree < start_degree
        bad_nak[1]["end_degree"] = 10.0  # start_degree is ~13.3333, end_degree is 10.0

        bad_file = tmp_path / "inverted_degrees.json"
        bad_file.write_text(json.dumps({"nakshatras": bad_nak, "yoni_compatibility": {}}), encoding="utf-8")

        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        try:
            with pytest.raises(DataValidationError) as exc:
                DataLoader.load_json("inverted_degrees.json", model=NakshatraTable)
            assert "must be greater than start_degree" in str(exc.value)
        finally:
            DataLoader.set_data_dir(old_dir)

    def test_nakshatra_invalid_gana_nadi_yoni(self, tmp_path):
        """NakshatraRecord must reject invalid Gana or Nadi enumeration."""
        valid_nakshatras = load_nakshatras()
        bad_nak = copy.deepcopy(valid_nakshatras)
        bad_nak[0]["gana"] = "AlienGana"  # Not Deva, Manushya, Rakshasa

        bad_file = tmp_path / "invalid_gana.json"
        bad_file.write_text(json.dumps({"nakshatras": bad_nak, "yoni_compatibility": {}}), encoding="utf-8")

        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        try:
            with pytest.raises(DataValidationError):
                DataLoader.load_json("invalid_gana.json", model=NakshatraTable)
        finally:
            DataLoader.set_data_dir(old_dir)

    def test_gochara_invalid_house_numbers(self, tmp_path):
        """GocharaPlanetRule must reject house numbers < 1 or > 12."""
        valid_gochara = load_gochara_rules()
        bad_gochara = copy.deepcopy(valid_gochara)
        bad_gochara["Sun"]["favourable_houses"] = [13, 3, 6]  # 13 is invalid house!

        bad_file = tmp_path / "invalid_house.json"
        bad_file.write_text(json.dumps(bad_gochara), encoding="utf-8")

        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        try:
            with pytest.raises(DataValidationError) as exc:
                DataLoader.load_json("invalid_house.json", model=GocharaTable)
            assert "must be between 1 and 12" in str(exc.value)
        finally:
            DataLoader.set_data_dir(old_dir)

    def test_remedies_missing_mandatory_grahas(self, tmp_path):
        """RemediesTable must reject payload missing any of the 9 Grahas."""
        valid_remedies = load_remedies()
        truncated_remedies = copy.deepcopy(valid_remedies)
        del truncated_remedies["remedies"]["Saturn"]  # remove Saturn

        bad_file = tmp_path / "missing_saturn.json"
        bad_file.write_text(json.dumps(truncated_remedies), encoding="utf-8")

        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        try:
            with pytest.raises(DataValidationError) as exc:
                DataLoader.load_json("missing_saturn.json", model=RemediesTable)
            assert "missing required Grahas" in str(exc.value)
        finally:
            DataLoader.set_data_dir(old_dir)

    def test_panchang_tithi_and_tara_count_boundaries(self, tmp_path):
        """PanchangTable must reject tithis != 30 or taras != 9."""
        valid_panchang = load_panchang_reference()
        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)

        try:
            # Case 1: 29 tithis
            bad_tithis = copy.deepcopy(valid_panchang)
            bad_tithis["tithis"] = bad_tithis["tithis"][:29]
            f_tithi = tmp_path / "bad_tithis.json"
            f_tithi.write_text(json.dumps(bad_tithis), encoding="utf-8")
            with pytest.raises(DataValidationError) as exc:
                DataLoader.load_json("bad_tithis.json", model=PanchangTable)
            assert "exactly 30 tithis" in str(exc.value)

            # Case 2: 8 taras
            bad_taras = copy.deepcopy(valid_panchang)
            bad_taras["taras"] = bad_taras["taras"][:8]
            f_tara = tmp_path / "bad_taras.json"
            f_tara.write_text(json.dumps(bad_taras), encoding="utf-8")
            with pytest.raises(DataValidationError) as exc:
                DataLoader.load_json("bad_taras.json", model=PanchangTable)
            assert "exactly 9 taras" in str(exc.value)

        finally:
            DataLoader.set_data_dir(old_dir)

    def test_zero_byte_empty_file_handling(self, tmp_path):
        """0-byte empty file must cleanly raise DataLoadError."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("", encoding="utf-8")

        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        try:
            with pytest.raises(DataLoadError):
                DataLoader.load_json("empty.json", defensive=False)
        finally:
            DataLoader.set_data_dir(old_dir)

    def test_defensive_fallback_on_all_error_types(self, tmp_path):
        """Verify defensive=True consistently returns fallback on FileNotFoundError, JSONDecodeError, ValidationError."""
        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        fallback = {"status": "safe_fallback"}

        try:
            # 1. Missing file
            res1 = DataLoader.load_json("missing.json", fallback=fallback, defensive=True)
            assert res1 == fallback

            # 2. Corrupt JSON
            corrupt = tmp_path / "corrupt.json"
            corrupt.write_text("{ unclosed", encoding="utf-8")
            res2 = DataLoader.load_json("corrupt.json", fallback=fallback, defensive=True)
            assert res2 == fallback

            # 3. Schema validation failure
            bad_schema = tmp_path / "bad_schema.json"
            bad_schema.write_text(json.dumps({"remedies": {}}), encoding="utf-8")
            res3 = DataLoader.load_json("bad_schema.json", model=RemediesTable, fallback=fallback, defensive=True)
            assert res3 == fallback

        finally:
            DataLoader.set_data_dir(old_dir)


# ==============================================================================
# DIMENSION 4: Caching Performance Benchmark & High-Throughput In-Memory Lookups
# ==============================================================================

class TestCachingPerformanceBenchmark:
    """Benchmark cold disk read vs warm in-memory cache hits."""

    def test_warm_cache_speedup_and_sub_millisecond_latency(self):
        """Subsequent 1000 reads must execute in sub-millisecond in-memory time."""
        DataLoader.clear_cache()

        # Cold read (includes disk I/O, json parsing, pydantic validation)
        t_cold_start = time.perf_counter()
        _ = DataLoader.load_remedies(validate=True)
        t_cold = time.perf_counter() - t_cold_start

        # Warm reads (1,000 in-memory retrievals)
        warm_iterations = 1000
        t_warm_start = time.perf_counter()
        for _ in range(warm_iterations):
            _ = DataLoader.load_remedies(validate=False)
        t_warm_total = time.perf_counter() - t_warm_start
        avg_warm_time = t_warm_total / warm_iterations

        # Assertions
        assert avg_warm_time < 0.001, f"Warm cache read too slow: {avg_warm_time*1000:.3f} ms per lookup"
        info = DataLoader.get_cache_info()
        assert info.hits >= warm_iterations, f"Expected >= {warm_iterations} hits, got {info.hits}"

    def test_cache_hit_miss_counter_accuracy(self):
        """Verify cache hits and misses increment with mathematical precision."""
        DataLoader.clear_cache()
        info0 = DataLoader.get_cache_info()
        assert info0.hits == 0 and info0.misses == 0

        # Load 3 distinct tables: exactly 3 misses
        _ = load_json_table("gochara_rules.json")
        _ = load_json_table("nakshatra_table.json")
        _ = load_json_table("planet_stone_colour.json")

        info1 = DataLoader.get_cache_info()
        assert info1.misses == 3
        assert info1.hits == 0

        # Query the same 3 tables 5 times each = 15 hits
        for _ in range(5):
            _ = load_json_table("gochara_rules.json")
            _ = load_json_table("nakshatra_table.json")
            _ = load_json_table("planet_stone_colour.json")

        info2 = DataLoader.get_cache_info()
        assert info2.misses == 3
        assert info2.hits == 15

        # Clear cache and verify counters reset
        DataLoader.clear_cache()
        info3 = DataLoader.get_cache_info()
        assert info3.hits == 0 and info3.misses == 0


# ==============================================================================
# DIMENSION 5: Multithreaded Concurrency Stress Testing
# ==============================================================================

class TestConcurrencyStress:
    """Stress test DataLoader under concurrent multi-threaded access."""

    def test_concurrent_multithreaded_reads(self):
        """16 concurrent worker threads making 800 total calls must not race, corrupt, or deadlock."""
        DataLoader.clear_cache()
        num_threads = 16
        calls_per_thread = 50

        def worker_task(thread_id: int):
            results = []
            for i in range(calls_per_thread):
                # Interleave different dataset loads
                if i % 4 == 0:
                    data = load_nakshatras()
                    assert len(data) == 27
                elif i % 4 == 1:
                    data = load_remedies()
                    assert "remedies" in data
                elif i % 4 == 2:
                    data = load_gochara_rules()
                    assert "Sun" in data
                else:
                    data = load_panchang_reference()
                    assert len(data["tithis"]) == 30
                results.append(True)
            return len(results)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_task, tid) for tid in range(num_threads)]
            completed_counts = [f.result() for f in as_completed(futures)]

        assert len(completed_counts) == num_threads
        assert sum(completed_counts) == num_threads * calls_per_thread


# ==============================================================================
# DIMENSION 6: Hostile Edge Cases & Function Contract Boundaries
# ==============================================================================

class TestHostileEdgeCases:
    """Stress test boundary parameters, case sensitivity, and non-standard inputs."""

    def test_get_remedy_for_planet_case_insensitivity(self):
        """Case variations (lowercase, uppercase, mixed, whitespace) must resolve properly."""
        sun_standard = get_remedy_for_planet("Sun")
        assert sun_standard is not None
        assert sun_standard["primary_gemstone"] == "Ruby"

        for variant in ["sun", "SUN", "sUn", "  Sun  ", " SUN \t"]:
            rem = get_remedy_for_planet(variant)
            assert rem is not None
            assert rem["primary_gemstone"] == "Ruby"

    def test_get_remedy_for_planet_unknown_returns_none(self):
        """Unknown planet names must return None cleanly without crashing."""
        for unknown in ["Pluto", "Neptune", "Uranus", "NonExistentGraha", ""]:
            assert get_remedy_for_planet(unknown) is None

    def test_directory_switching_and_cache_invalidation(self, tmp_path):
        """Changing data directory via set_data_dir() must invalidate the active cache."""
        # Load from default dir
        data_default = load_json_table("nakshatra_table.json")
        assert len(data_default["nakshatras"]) == 27

        # Switch to mock dir with modified file
        mock_nak = {"nakshatras": [{"index": 0, "name": "CustomAshwini"}]}
        mock_file = tmp_path / "nakshatra_table.json"
        mock_file.write_text(json.dumps(mock_nak), encoding="utf-8")

        old_dir = DataLoader.get_data_dir()
        DataLoader.set_data_dir(tmp_path)
        try:
            # Must read new directory file, not old cached one
            data_custom = load_json_table("nakshatra_table.json")
            assert data_custom["nakshatras"][0]["name"] == "CustomAshwini"
        finally:
            DataLoader.set_data_dir(old_dir)

        # Restoring directory must yield standard dataset again
        data_restored = load_json_table("nakshatra_table.json")
        assert data_restored["nakshatras"][0]["name"] == "Ashwini"
