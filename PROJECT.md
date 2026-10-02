# Project: AstroGuide

## Architecture

AstroGuide is an astrology web application and conversational assistant combining deterministic astrological calculations (using Swiss Ephemeris and classical Jyotish tables), external astrology MCP services, a Corrective Retrieval-Augmented Generation (CRAG) knowledge pipeline, and a modern glassmorphic web UI.

### Data & Control Flow
1. **Frontend / Web Client (`static/`)**: User interacts with web UI tabs. Makes REST fetch requests to FastAPI backend (`server.py`).
2. **API Layer (`server.py`)**: Validates request models with Pydantic, routes to core calculation tools (`astroguide/tools/`), RAG search, and health endpoints.
3. **Astrology Tool Suite (`astroguide/tools/`)**:
   - `birth_chart.py`: Swiss Ephemeris planetary positions, ascendant, house cusps, SVG chart rendering.
   - `daily_transits.py`: Gochara transit scoring with Vedha pair obstruction analysis.
   - `numbers_stones.py`: Pythagorean/Vedic Driver & Conductor numbers, gemstone, colour, and remedy lookups.
   - `compatibility.py`: Ashtakoota 36-point Guna Milan matching with symmetric Yoni evaluation.
   - `find_dates.py`: Multi-day muhurtha evaluation (Tithi, Chandrabala, Tarabala, Rahu Kalam).
   - `rag_search.py`: Knowledge base retrieval over astrological notes and tables.
4. **Data & Table Repository (`data/`)**:
   - `data/tables/`: Static JSON tables (`gochara_rules.json`, `nakshatra_table.json`, `planet_stone_colour.json`, `astrological_remedies.json`, `panchang_reference.json`).
   - `data/astrology_notes/`: Markdown knowledge base articles on Zodiac signs, Nakshatras, and remedies.
   - `data/chroma_db/`: Local persistent Chroma vector store for hybrid dense+lexical CRAG search.
5. **CRAG Architecture (`astroguide/rag/pipeline/`)**:
   - Ingestor (`ingestor.py`) chunks documents into parent-child hierarchies and embeds via `all-MiniLM-L6-v2`.
   - Hybrid Retriever (`retriever.py`) combines dense semantic search + BM25 + Reciprocal Rank Fusion (RRF) + MMR + Cross-Encoder reranking.
   - Self-Healing Agent (`agent.py`) with Contextual Bandit policy (`bandit_policy.py`) selecting direct generation, query rewrite, or fallback search.
6. **Astrology MCP Integration (`astroguide/tools/mcp_adapter.py`)**:
   - Connects to the local 111-tool `astrology` MCP server with graceful offline fallback to local calculations.

---

## Feature Inventory

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Astrological Remedies Dataset | Curate `data/tables/astrological_remedies.json` with 9 planetary remedies (gemstones, metals, mantras, deities, charity, lifestyle) | M1 | Survey (Explorer 2) |
| F2 | Panchang Reference Dataset | Curate `data/tables/panchang_reference.json` externalizing Tithis, Taras, and Muhurtha rules | M1 | Survey (Explorer 2) |
| F3 | Astrology Knowledge Base Notes | Curate `data/astrology_notes/zodiac_signs.md` and `nakshatras_guide.md` for RAG | M1 | Survey (Explorer 1 & 2) |
| F4 | Robust Cached Data Loader | Implement `astroguide/utils/data_loader.py` with `@lru_cache`, UTF-8 encoding, and schema validation | M1 | Survey (Explorer 2) |
| F5 | Server Health Check Endpoint | Add `GET /health` and `GET /api/health` returning HTTP 200 `{"status": "ok"}` | M2 | Survey (Explorer 3) |
| F6 | Systematic Bug Fix: Yoni Symmetry | Fix asymmetric Goat vs Monkey scoring in `compatibility.py` | M2 | Survey (Explorer 3) |
| F7 | Systematic Bug Fix: Birth Time Seconds | Support `%H:%M:%S` alongside `%H:%M` in `birth_chart.py` | M2 | Survey (Explorer 3) |
| F8 | Systematic Bug Fix: Clean server.py Imports | Remove aggressive `sys.modules['langchain_core']` clobbering in `server.py` | M2 | Survey (Explorer 3) |
| F9 | Systematic Bug Fix: CLI Import Fix | Fix `pipeline.config` import in `main.py` | M2 | Survey (Explorer 3) |
| F10 | Systematic Bug Fix: numbers_stones TypeError | Safely validate `birth_date` and handle non-string / invalid inputs gracefully | M2 | Survey (Explorer 3) |
| F11 | UI Form UX: Dropdown Selectors | Replace raw integer inputs (0-11, 0-26) with human-readable `<select>` dropdowns | M2 | Survey (Explorer 3) |
| F12 | UI Result Display: Card Formatting | Render structured cards/tables for compatibility, transits, and numbers instead of raw `<pre>` dumps | M2 | Survey (Explorer 3) |
| F13 | Chroma DB Path Harmonization | Update `PipelineConfig.chroma_db_dir` to point to project-relative `data/chroma_db` | M3 | Survey (Explorer 1 & 2) |
| F14 | Knowledge Base Vector Ingestion | Ingestion script embedding `data/astrology_notes/` into local Chroma vector store | M3 | Survey (Explorer 1) |
| F15 | RAG Search Tool | Implement `astroguide/tools/rag_search.py` and register in `ALL_TOOLS` | M3 | Survey (Explorer 1) |
| F16 | Astrology MCP Adapter | Implement `astroguide/tools/mcp_adapter.py` connecting to astrology MCP tools with local fallback | M3 | Survey (Explorer 1) |
| F17 | Dual-Track Pytest Suite Expansion | Expand pytest suite across `tests/unit/` and `tests/scenarios/` covering all tools, server, datasets, RAG | E2E Track / M4 | Survey (Explorer 3) |
| F18 | Server HTTP Validation & Launch Check | Verify local server launches and passes live health check / queries with HTTP 200 | M4 | ORIGINAL_REQUEST |
| F19 | Adversarial Coverage Hardening | White-box stress-testing of edge cases, boundaries, and concurrency | M4 Phase 2 | Project Pattern |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Dataset Acquisition & Data Loading Architecture | Curate `astrological_remedies.json`, `panchang_reference.json`, `data/astrology_notes/*.md`; build centralized data loader with caching and UTF-8 verification. Satisfies R1. | none | IN_PROGRESS |
| M2 | Web Server, UI Enhancements & Systematic Bug Fixes | Implement `/health` endpoint, fix Yoni symmetry, birth_time parsing, `server.py` imports, `main.py` import, and improve UI with dropdown selectors and card display. Document root-cause analysis for bugs. Satisfies R3. | M1 | PLANNED |
| M3 | RAG Pipeline Integration & MCP Adapter | Connect Chroma DB to `data/chroma_db`, ingest astrology knowledge base, build `rag_search` tool, and implement astrology MCP adapter. | M1, M2 | PLANNED |
| M4 | Final Milestone: Full E2E Test Pass & Adversarial Hardening | Phase 1: Pass 100% of E2E tests (Tiers 1-4). Phase 2: Adversarial coverage hardening (Tier 5). Verify all acceptance criteria and server HTTP 200 response. | M1, M2, M3, E2E Track | PLANNED |

### Parallel Track: E2E Testing Track
- **Owner**: E2E Testing Orchestrator / Subagents
- **Scope**: Requirement-driven, opaque-box test suite spanning Tiers 1-4. Creates `TEST_INFRA.md` and publishes `TEST_READY.md`.
- **Status**: IN_PROGRESS

---

## Interface Contracts

### `astroguide.utils.data_loader` ↔ Tools & Server
```python
def load_json_table(filename: str) -> dict:
    """Loads a JSON file from data/tables/ with LRU caching and explicit UTF-8."""

def load_remedies() -> dict:
    """Returns astrological remedies for all 9 grahas."""

def load_nakshatras() -> list:
    """Returns list of 27 nakshatra dictionaries."""

def load_gochara_rules() -> dict:
    """Returns Gochara transit rules and Vedha pairs."""
```

### `server.py` ↔ Client / External Monitors
```http
GET /health
Response: 200 OK {"status": "ok", "service": "astroguide", "version": "1.0.0"}

GET /api/health
Response: 200 OK {"status": "ok", "service": "astroguide", "version": "1.0.0"}

POST /api/birth_chart
Request: BirthChartRequest
Response: 200 OK {"success": bool, "data": {...}}

POST /api/compatibility
Request: CompatibilityRequest
Response: 200 OK {"success": bool, "data": {"total_points": float, "guna_details": {...}}}
```

### `astroguide.tools.rag_search` ↔ Agent & Server
```python
@tool
def rag_search(query: str, top_k: int = 5) -> dict:
    """Performs hybrid retrieval over astrology knowledge base and returns top parent chunks."""
```

---

## Code Layout

- `astroguide/`
  - `tools/`: Astrological calculation tools (`birth_chart.py`, `compatibility.py`, `daily_transits.py`, `find_dates.py`, `numbers_stones.py`, `rag_search.py`, `mcp_adapter.py`)
  - `rag/pipeline/`: CRAG components (`chunking.py`, `config.py`, `ingestor.py`, `retriever.py`, `agent.py`, `bandit_policy.py`)
  - `utils/`: Common utilities (`data_loader.py`)
- `data/`
  - `tables/`: Structured JSON tables (`gochara_rules.json`, `nakshatra_table.json`, `planet_stone_colour.json`, `astrological_remedies.json`, `panchang_reference.json`)
  - `astrology_notes/`: Curated Markdown domain texts for RAG
  - `chroma_db/`: Persisted vector database
- `static/`
  - `index.html`, `script.js`, `style.css`
- `tests/`
  - `conftest.py`, `pytest.ini`
  - `unit/`: Unit tests for tools, data loaders, and models
  - `scenarios/`: End-to-end API scenario tests and RAG tests
  - `test_reproduction_fixes.py`: Legacy fix verification tests
- Root files:
  - `server.py`, `main.py`, `requirements.txt`, `PROJECT.md`, `TEST_INFRA.md`, `TEST_READY.md`
