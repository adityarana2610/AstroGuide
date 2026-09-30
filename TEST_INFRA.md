# AstroGuide Testing Infrastructure & 4-Tier Methodology Specification

**Project**: AstroGuide (Vedic Astrology Web Application & Conversational Assistant)  
**Author**: E2E Test Suite Architect (`test_writer_e2e_1`)  
**Status**: Active & Implemented  
**Date**: 2026-09-30  
**Version**: 1.0.0  

---

## 1. Executive Summary & Architecture Overview

AstroGuide combines deterministic astrological calculations (Swiss Ephemeris, classical Jyotish tables, Ashtakoota matching, Gochara transits, Muhurtha selection), external astrology MCP services, a Corrective Retrieval-Augmented Generation (CRAG) knowledge pipeline, and a modern glassmorphic web UI.

To guarantee mathematical precision, interface stability, and failure resilience, the testing infrastructure follows a comprehensive **4-Tier Testing Methodology** executed via **Pytest**, **FastAPI TestClient**, and **Pydantic** validation models.

```
                            +-------------------------------------------+
                            |       Tier 4: Real-World Scenarios        |
                            |   (End-to-End Client Consultation Flows)  |
                            +-------------------------------------------+
                                                  |
                            +-------------------------------------------+
                            |     Tier 3: Cross-Feature Pairwise        |
                            |    (Birth Chart -> Transits -> Remedies)  |
                            +-------------------------------------------+
                                                  |
                            +-------------------------------------------+
                            |       Tier 2: Boundary & Corner Cases     |
                            |   (Out-of-bounds, Inverted Dates, Errors) |
                            +-------------------------------------------+
                                                  |
                            +-------------------------------------------+
                            |        Tier 1: Feature Coverage           |
                            |  (Tools Unit, Data Tables, API Endpoints) |
                            +-------------------------------------------+
```

---

## 2. Test Suite Directory Layout

All tests and testing assets reside within the `tests/` directory and root configuration files:

```
f:\AstroGuide\
├── pytest.ini                            # Global Pytest configuration and markers
├── TEST_INFRA.md                         # This architecture specification
├── TEST_READY.md                         # Test readiness, execution commands, and pass status
└── tests\
    ├── __init__.py                       # Package declaration
    ├── conftest.py                       # Shared fixtures, client factory, mock data
    ├── test_reproduction_fixes.py        # Verified regression tests for ISS-01 to ISS-12
    ├── unit\
    │   ├── __init__.py
    │   ├── test_data_loader.py           # Unit tests for JSON table schemas & data loader
    │   └── test_tools.py                 # Unit tests for all 5 core astrology tools
    └── scenarios\
        ├── __init__.py
        ├── test_api_endpoints.py         # End-to-end HTTP API tests (happy, error, pairwise)
        └── test_health.py                # Server health checks and static asset serving
```

---

## 3. The 4-Tier Testing Methodology

### Tier 1: Feature Coverage (Core Functional Capabilities)
Verifies the nominal primary paths (happy paths) for every tool, dataset, and server endpoint:

1. **Astrology Tool Suite (`tests/unit/test_tools.py`)**:
   - `birth_chart`: Calculates exact planetary positions (Sun through Ketu), Ascendant sign/degree, 12 whole sign houses, and renders North/South Indian SVG diagrams.
   - `numbers_stones`: Single-digit Pythagorean/Vedic Driver & Conductor numbers, gemstone associations, and primary lucky numbers.
   - `daily_transits`: Evaluates Gochara planetary transit houses against natal Moon sign, scores favourable/unfavourable transits, and calculates overall daily score.
   - `compatibility`: Complete 36-point Ashtakoota Guna Milan across all 8 kootas (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi).
   - `find_dates`: Evaluates multi-day Muhurtha windows scoring Tithi, Chandrabala, Tarabala, and Rahu Kalam.
2. **Data & Table Repository (`tests/unit/test_data_loader.py`)**:
   - Validates UTF-8 encoding and schema compliance for `data/tables/nakshatra_table.json` (all 27 nakshatras with deities, ganas, nadis, yonis).
   - Validates `data/tables/gochara_rules.json` (all 9 Grahas with favourable/unfavourable houses and Vedha pairs).
   - Validates `data/tables/planet_stone_colour.json` (digits 1–9 mapped to planets, stones, and friendly numbers).
3. **Web Server REST APIs (`tests/scenarios/test_api_endpoints.py`, `tests/scenarios/test_health.py`)**:
   - HTTP POST `/api/birth_chart`, `/api/numbers_stones`, `/api/find_dates`, `/api/daily_transits`, `/api/compatibility` returning status 200 with `success: True`.
   - Root endpoint `GET /` serving HTML single-page app.
   - Static assets `GET /static/style.css` and `GET /static/script.js` returning HTTP 200.

### Tier 2: Boundary, Corner & Adversarial Edge Cases
Stresses the system with boundary inputs, out-of-bounds parameters, and invalid data combinations to ensure no unhandled exceptions or crashes occur:

1. **Input Range Boundaries (`tests/unit/test_tools.py`, `tests/scenarios/test_api_endpoints.py`)**:
   - Moon sign indices `< 0` or `>= 12`.
   - Nakshatra indices `< 0` or `>= 27`.
   - Moon pada `< 1` or `> 4`.
   - Inverted date ranges in Muhurtha finder (`end_date < start_date`).
   - Non-existent calendar dates (`2026-02-30`).
   - Malformed date/time strings (`"invalid-date"`, missing time components).
2. **Schema & Protocol Rejections**:
   - FastAPI/Pydantic rejects missing required fields and schema violations with HTTP 422 Unprocessable Entity.
   - Semantic calculation errors within tools return HTTP 200 with `{"success": False, "error": "<message>"}` instead of 500 Server Crashes.
3. **Encoding & Parsing Integrity (`tests/unit/test_data_loader.py`)**:
   - Multibyte Unicode symbols (Sanskrit Om `ॐ`, zodiac glyphs `♈-♓`, Devanagari script) load without `UnicodeDecodeError`.
   - Malformed JSON syntax triggers clean `json.JSONDecodeError` rather than silent corruption.

### Tier 3: Cross-Feature Pairwise Integration
Validates workflows where the output of one component becomes the input of another, ensuring interface contracts are honored across module boundaries:

1. **Birth Chart → Daily Transits**:
   - Client requests a birth chart calculation.
   - Moon's calculated sign index and degree are extracted from the birth chart.
   - Extracted Moon parameters are piped into `/api/daily_transits` to compute personalized Gochara transits.
2. **Birth Chart → Numerology & Gemstones**:
   - Client calculates birth chart.
   - Extracted birth date is piped into `/api/numbers_stones` to obtain Driver/Conductor numbers and gemstones.
3. **Centralized Data Loader Integration**:
   - LRU caching verification: subsequent reads return identical cached objects without repetitive disk I/O.
   - Caching statistics (`cache_info.hits`) increment on repeated accesses.

### Tier 4: Real-World Scenarios & User Journeys
Simulates complete real-world astrology consultations matching the user requirements:

1. **Full Marriage Consultation Journey (`tests/scenarios/test_api_endpoints.py:test_real_world_marriage_consultation_journey`)**:
   - Step 1: Calculate Bridegroom's numerology, lucky numbers, and gemstone.
   - Step 2: Calculate Bride's numerology, lucky numbers, and gemstone.
   - Step 3: Run 36-point Ashtakoota compatibility between their natal nakshatras (e.g., Rohini vs. Uttara Phalguni).
   - Step 4: Scan candidate wedding dates across a 5-day window for auspicious Muhurtha.
   - Step 5: Check daily planetary transits on the selected wedding date to verify favourable planetary support.

---

## 4. Expected Output Derivation & Authoritative Sources

Every test assertion in AstroGuide is derived from explicit authoritative sources:

| Feature / Domain | Test Input | Authoritative Oracle Source | Expected Output Criteria |
|---|---|---|---|
| **Birth Chart** | `1990-05-15 14:30`, Lat 28.6139, Lon 77.2090 | Swiss Ephemeris (`swisseph`) & Lahiri Ayanamsha | Exactly 9 planets; Ascendant in [0, 11]; 12 houses; valid SVG containing `<svg>` and `polygon`/`rect` tags. |
| **Numerology** | `1995-10-15` | Pythagorean Single-Digit Reduction / Cheiro | Day 15 -> 1+5 = 6 (Venus); Full date 1+9+9+5+1+0+1+5 = 31 -> 3+1 = 4 (Rahu); Lucky numbers contain [6, 4] deduplicated. |
| **Daily Transits** | Sign 0 (Aries), `2026-10-01` | Classical Gochara Rules (`gochara_rules.json`) | 9 planets with `is_favourable` and `is_blocked_by_vedha` booleans; total score computed. |
| **Compatibility** | Nakshatra 0 (Ashwini) vs Nakshatra 23 (Shatabhisha) | Brihat Parashara Hora Shastra (BPHS) Ashtakoota | Horse (Male) vs Horse (Female) -> Yoni = 4.0 pts; Total points in [0, 36.0]; 8 kootas sum to total. |
| **Muhurtha** | Sign 0, Nakshatra 0, `2026-10-01` to `2026-10-03` | Panchang Calculation & Rahu Kalam rules | Evaluated list of 3 dates with Tithi, score, and recommended actions. |
| **API Endpoints** | Valid JSON payloads | FastAPI / Starlette HTTP Specification | HTTP 200 with `{"success": True, "data": {...}}`. |
| **API Errors** | Bad date strings / out of bounds inputs | `PROJECT.md § Interface Contracts` & `server.py` | HTTP 200 with `{"success": False, "error": "<msg>"}` or HTTP 422 for schema invalidation. |

---

## 5. Test Configuration & Fixtures

### `pytest.ini` Configuration
- `testpaths = tests`: Automatically discovers tests in `tests/unit/`, `tests/scenarios/`, and `tests/test_reproduction_fixes.py`.
- `markers`: Custom markers for `unit`, `scenario`, `reproduction`, `tier1`, `tier2`, `tier3`, and `tier4`.
- `addopts = -v --tb=short`: Verbose output with concise tracebacks.

### Shared Fixtures (`tests/conftest.py`)
- `client`: Session-scoped `starlette.testclient.TestClient(server.app)` for fast, in-memory HTTP API testing without spawning external network listeners.
- `valid_birth_chart_payload`: Pre-configured valid birth chart dictionary.
- `valid_numbers_stones_payload`: Pre-configured valid numbers and stones dictionary.
- `valid_find_dates_payload`: Pre-configured valid Muhurtha search dictionary.
- `valid_daily_transits_payload`: Pre-configured valid Gochara transit dictionary.
- `valid_compatibility_payload`: Pre-configured valid Ashtakoota compatibility dictionary.
- `temp_data_dir`: Temporary directory populated with isolated mock reference tables for testing loading and fault-tolerance without touching repository files.

---

## 6. How to Run the Tests

### Full Test Suite Execution
```powershell
pytest
```

### Run by Tier
```powershell
# Run Tier 1 (Feature Coverage)
pytest -m tier1

# Run Tier 2 (Boundary & Corner Cases)
pytest -m tier2

# Run Tier 3 (Cross-Feature Pairwise)
pytest -m tier3

# Run Tier 4 (Real-World Scenarios)
pytest -m tier4
```

### Run by Scope
```powershell
# Run Unit Tests only
pytest tests/unit/

# Run Scenario & Integration Tests only
pytest tests/scenarios/

# Run Verified Reproduction & Regression Tests only
pytest tests/test_reproduction_fixes.py
```

---

## 7. Progressive Testability & Milestone Dependencies

In strict compliance with teamwork protocols:
- Tests for completed/existing features (all 5 core tools, existing JSON reference tables, all 5 HTTP endpoints, root UI delivery) are fully active and execute cleanly.
- Tests for pending milestone features:
  - `astroguide.utils.data_loader` (Milestone M1 / Feature F4): Evaluated with conditional availability checks (`pytest.skip` if module is not yet imported), while all underlying table integrity tests execute immediately.
  - Dedicated `/health` endpoint (Milestone M2 / Feature F5): Evaluated with graceful skip until implemented in `server.py`.
  - Once subsequent milestone agents implement these features, the test suite verifies them immediately with zero test code modifications.
