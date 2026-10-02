# AstroGuide: Authoritative Astrological & Numerological Datasets for Chroma RAG

This document compiles high-quality, authoritative open datasets, computational libraries, and reference repositories to expand and enrich the **Chroma Vector Knowledge Base** in **AstroGuide** (an agentic astrology and numerology assistant).

Every dataset has been verified for existence, accessibility, and compatibility with AstroGuide’s **Self-Healing Corrective RAG (CRAG)** pipeline, which leverages:
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors)
- **Hybrid Retrieval**: BM25 lexical search + Dense semantic search with Reciprocal Rank Fusion (RRF, $k=60$)
- **Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Parent-Child Chunking**: Fine-grained children for retrieval expanded to parent sections (soft max 900 characters)
- **Self-Healing Contextual Bandit**: LinUCB policy deciding between Direct Generation, Query Rewrite, and External Search
- **Strict Separation of Concerns**: Deterministic code computes astronomical/numerological facts, while LLM retrieves context and narrates with enforced positivity.

---

## Table of Contents
1. [Planetary Ephemeris, Celestial Coordinates & Astronomical Datasets](#1-planetary-ephemeris-celestial-coordinates--astronomical-datasets)
2. [Western Zodiac, Houses, Aspects & Archetype Datasets](#2-western-zodiac-houses-aspects--archetype-datasets)
3. [Numerology Systems (Pythagorean, Chaldean & Kabbalistic)](#3-numerology-systems-pythagorean-chaldean--kabbalistic)
4. [Vedic Astrology (Jyotish) Nakshatras, Rashis & Dasha Systems](#4-vedic-astrology-jyotish-nakshatras-rashis--dasha-systems)
5. [Open Multi-Disciplinary Datasets (Hugging Face, Kaggle & GitHub)](#5-open-multi-disciplinary-datasets-hugging-face-kaggle--github)
6. [Chroma RAG Integration & Ingestion Architecture](#6-chroma-rag-integration--ingestion-architecture)
7. [Dataset Comparison & Verification Matrix](#7-dataset-comparison--verification-matrix)
8. [Licensing, Ethical Guidelines & Disclaimers](#8-licensing-ethical-guidelines--disclaimers)

---

## 1. Planetary Ephemeris, Celestial Coordinates & Astronomical Datasets

### 1.1 Swiss Ephemeris Data Files & Source Code (Astrodienst AG)
- **Source Name**: Swiss Ephemeris (`swisseph`)
- **Verified URLs**:
  - Documentation: [https://www.astro.com/swisseph/swephinfo_e.htm](https://www.astro.com/swisseph/swephinfo_e.htm)
  - GitHub Repository: [https://github.com/aloistr/swisseph](https://github.com/aloistr/swisseph)
  - Ephemeris Data Files: [https://github.com/aloistr/swisseph/tree/master/ephe](https://github.com/aloistr/swisseph/tree/master/ephe)
- **Data Type & Format**: Binary ephemeris compressed tables (`.se1` files: `sepm*.se1`, `semo*.se1`, `seas*.se1`), C source code, technical documentation.
- **Detailed Description**:
  Developed by Dr. Alois Treindl and Dieter Koch of Astrodienst AG, the Swiss Ephemeris is the gold standard astronomical calculation engine for astrology. It compresses NASA JPL Numerical Integration Ephemerides (DE431/DE406) and the semi-analytical planetary theory Moshier/VSOP87 over a 10,800-year span (-5400 to +5400). It computes ecliptic longitude, latitude, distance, speed, sidereal ayanamsas (Lahiri, Krishnamurti, Raman, Fagan/Bradley), house cusps (Placidus, Koch, Whole Sign, Equal, Regiomontanus), and planetary nodes.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Extract technical documentation chapters on ayanamsa calculations, planetary speeds, retrograde stations, and coordinate transformations into Markdown files in `data/astrology_notes/`.
  - *Chunking Strategy*: Parent-child section chunking (`max_chars=900`) keyed on algorithm titles (`Ayanamsa Formulae`, `True vs Mean Nodes`, `House Cusp Systems`).
  - *Metadata Tagging*:
    ```json
    {
      "source": "swisseph",
      "category": "astronomical_computation",
      "topic": "sidereal_ayanamsa",
      "subtopic": "lahiri_chitra_paksha",
      "access_level": "technical_reference"
    }
    ```
  - *Query Patterns*: "How is Lahiri ayanamsa calculated in sidereal astrology?", "Difference between Placidus and Whole Sign house cusps", "How are retrograde planetary speeds determined?"
- **Licensing & Access**: Dual licensing: GNU GPL v2 for open-source / non-commercial applications; professional commercial license available from Astrodienst AG.

---

### 1.2 pyswisseph (Python Swiss Ephemeris Extension)
- **Source Name**: `pyswisseph`
- **Verified URLs**:
  - PyPI: [https://pypi.org/project/pyswisseph/](https://pypi.org/project/pyswisseph/)
  - GitHub: [https://github.com/astronexus/pyswisseph](https://github.com/astronexus/pyswisseph)
- **Data Type & Format**: Python C-Extension wrapper, API documentation, Python interface tables.
- **Detailed Description**:
  The official Python binding for the Swiss Ephemeris library, developed by Thomas Mack and maintained by the Astronexus team. Directly invoked by AstroGuide's `astroguide/tools/` for deterministic chart computations (`swe.calc_ut()`, `swe.houses()`, `swe.set_sid_mode()`).
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Ingest API parameter references and planetary ID mapping constants (`SE_SUN=0`, `SE_MOON=1`, `SE_MARS=4`, etc.) and flag specifications (`SEFLG_SIDEREAL`, `SEFLG_SPEED`).
  - *Chunking Strategy*: Markdown tables converted to Docling table nodes.
  - *Metadata Tagging*:
    ```json
    {
      "source": "pyswisseph",
      "category": "api_reference",
      "tool": "get_birth_chart",
      "system": "sidereal_tropical"
    }
    ```
  - *Query Patterns*: "Which Swiss Ephemeris flag enables Lahiri sidereal calculations?", "How to resolve high-latitude house cusp anomalies in birth charts?"
- **Licensing & Access**: GNU GPL v2.

---

### 1.3 VSOP87 Analytical Planetary Ephemeris (CDS VizieR VI/81)
- **Source Name**: Variations Séculaires des Orbites Planétaires (VSOP87)
- **Verified URLs**:
  - CDS VizieR Astronomical Catalogue: [https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=VI/81](https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=VI/81)
  - Multi-language Implementation: [https://github.com/gmiller123456/vsop87-multilang](https://github.com/gmiller123456/vsop87-multilang)
- **Data Type & Format**: ASCII trigonometric series coefficient tables (VSOP87A to VSOP87E), Python package.
- **Detailed Description**:
  Developed by Pierre Bretagnon and Gérard Francou at the Bureau des Longitudes / IMCCE, Paris. Computes heliocentric and barycentric planetary positions (Mercury to Neptune) with sub-arcsecond accuracy over 4,000 years around J2000. Provides the definitive mathematical ground truth for orbital mechanics used in standalone planetary tracking without binary ephemeris dependencies.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Overview of planetary orbital dynamics, periodic terms, and heliocentric to geocentric coordinate transformation guides.
  - *Chunking Strategy*: Parent chunks by planet; children chunks by coordinate element (longitude, latitude, radius vector).
  - *Metadata Tagging*:
    ```json
    {
      "source": "vsop87",
      "category": "orbital_mechanics",
      "body": "Jupiter",
      "coordinate_frame": "J2000_ecliptic"
    }
    ```
  - *Query Patterns*: "How to convert heliocentric coordinates to geocentric astrological positions?", "Accuracy limits of analytical planetary ephemerides".
- **Licensing & Access**: Public domain / Open academic use (CDS VizieR astronomical archives).

---

### 1.4 Astrology API Accuracy Benchmark Dataset
- **Source Name**: Astrology API Accuracy Benchmark (RoxyAPI)
- **Verified URL**: [https://github.com/RoxyAPI/astrology-api-benchmark](https://github.com/RoxyAPI/astrology-api-benchmark)
- **Data Type & Format**: JSON test fixtures, Python test suites, reference ephemeris outputs.
- **Detailed Description**:
  A rigorous benchmarking suite compiling real-world reference charts of famous personalities sourced from Astro-Databank (all graded with "AA" Rodden rating birth certificate data) and cross-verified against NASA JPL Horizons high-precision planetary coordinates. Contains exact degree, minute, and second positions for Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Rahu, Ketu, Ascendant, and Midheaven.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Ingest verification chart cases as reference question-answer pairs and benchmark validation documents.
  - *Chunking Strategy*: One chart per parent section containing individual planetary degree tables.
  - *Metadata Tagging*:
    ```json
    {
      "source": "astrology_api_benchmark",
      "category": "ground_truth_chart",
      "rodden_rating": "AA",
      "subject": "celebrity_reference_chart"
    }
    ```
  - *Query Patterns*: "Verify planetary degree for birth chart 1982-06-21 London", "NASA JPL ground truth for Moon position in Rohini".
- **Licensing & Access**: MIT License.

---

## 2. Western Zodiac, Houses, Aspects & Archetype Datasets

### 2.1 Kerykeion Astrological Calculation Engine & Model Schema
- **Source Name**: Kerykeion
- **Verified URL**: [https://github.com/g-battaglia/kerykeion](https://github.com/g-battaglia/kerykeion)
- **Data Type & Format**: Python library, Pydantic v2 data models, JSON schemas, SVG chart assets.
- **Detailed Description**:
  Authored by Giacomo Battaglia, Kerykeion is a comprehensive modern astrology library built on top of pyswisseph. It calculates natal charts, transit charts, synastry matrices, composite charts, and secondary progressions. It provides structured Pydantic schemas for planets, 12 zodiac signs, 12 houses (Placidus default), major aspects (conjunction, sextile, square, trine, opposition), and element/quality balances.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Aspect definitions, orb boundaries (e.g. major orbs: 8°-10°, minor: 2°-3°), planetary condition rules, and synastry compatibility models.
  - *Chunking Strategy*: Markdown sections organized by aspect type (`Trine: Flow and Harmonious Talents`, `Square: Growth through Creative Tension`).
  - *Metadata Tagging*:
    ```json
    {
      "source": "kerykeion",
      "tradition": "western_modern",
      "component": "aspect_matrix",
      "aspect_type": "trine",
      "orb_degrees": 8.0
    }
    ```
  - *Query Patterns*: "What does Sun trine Jupiter signify in a natal chart?", "How to interpret a Saturn square Moon transit?", "Synastry orb allowances for conjunctions".
- **Licensing & Access**: AGPL-3.0 License.

---

### 2.2 Flatlib Traditional Western Astrology Library & Correspondences
- **Source Name**: Flatlib
- **Verified URL**: [https://github.com/flatangle/flatlib](https://github.com/flatangle/flatlib)
- **Data Type & Format**: Python library, structured configuration dictionaries, dignity tables.
- **Detailed Description**:
  Flatlib is an open-source Python library dedicated to Traditional (Hellenistic, Medieval, and Renaissance) Western Astrology. It features algorithmic computations for essential dignities (Domicile/Rulership, Exaltation, Triplicity, Term, Face/Decan), accidental dignities (angular, succedent, cadent houses), planetary sects (diurnal vs nocturnal), Almuten calculations, and Arabic Parts (Lot of Fortune, Lot of Spirit).
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Essential dignity scoring tables (Ptolemaic and Egyptian term tables), triplicity rulers (Dorothean system), and planetary condition definitions.
  - *Chunking Strategy*: Tabular markdown nodes chunked by planet and sign dignity.
  - *Metadata Tagging*:
    ```json
    {
      "source": "flatlib",
      "tradition": "traditional_hellenistic",
      "component": "essential_dignities",
      "planet": "Saturn",
      "dignity_type": "exaltation_fall"
    }
    ```
  - *Query Patterns*: "Which signs are the exaltation and fall of Mars?", "Dorothean triplicity rulers for water signs", "Calculating the Part of Fortune for day vs night births".
- **Licensing & Access**: MIT License.

---

### 2.3 AstroGpt Structured Astrology Knowledge Base
- **Source Name**: AstroGpt
- **Verified URL**: [https://github.com/Varun-2538/AstroGpt](https://github.com/Varun-2538/AstroGpt)
- **Data Type & Format**: JSON knowledge files, Python pipeline.
- **Detailed Description**:
  A repository containing structured JSON datasets crafted specifically for LLM-based astrological conversational engines. Includes granular records for:
  - 12 Zodiac signs: Ruling planets, element (Fire, Earth, Air, Water), modality (Cardinal, Fixed, Mutable), body parts, psychological traits, shadow tendencies, and positive aspirations.
  - 12 Houses: Bhava significations (Karakatwas), classical life domains (1st: Identity, 2nd: Finances, 4th: Home/Mother, 7th: Partnerships, 10th: Career).
  - Planet in House & Planet in Sign interpretations: Complete combinatorial matrix of 9 planets $\times$ 12 houses $\times$ 12 signs.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Ingest directly into Chroma DB using AstroGuide's native `DoclingJSONIngestor`.
  - *Chunking Strategy*: Each JSON node represents a discrete fine-grained child chunk, mapped to a parent section representing the overarching sign/house archetype.
  - *Metadata Tagging*:
    ```json
    {
      "source": "astrogpt",
      "planet": "Jupiter",
      "house": 9,
      "zodiac_sign": "Sagittarius",
      "category": "placement_interpretation"
    }
    ```
  - *Query Patterns*: "Interpretation of Jupiter placed in 9th house", "Qualities of Scorpio rising with Mars in Aries", "Sun in Taurus 2nd house financial indicators".
- **Licensing & Access**: Open Source (Public GitHub Repository).

---

### 2.4 Astro-Databank Celebrity Birth Chart & Biography Archive
- **Source Name**: Astro-Databank (Astrodienst AG)
- **Verified URL**: [https://www.astro.com/astro-databank/Main_Page](https://www.astro.com/astro-databank/Main_Page)
- **Data Type & Format**: MediaWiki XML / HTML, structured biographical wiki entries.
- **Detailed Description**:
  Founded by Lois Rodden and maintained by Astrodienst AG, Astro-Databank is the premier research archive of astrological birth data, containing over 60,000 charts with verified birth certificates. Every entry features:
  - Exact birth time, date, latitude, longitude, and timezone.
  - **Rodden Rating**: "AA" (birth certificate in hand), "A" (memory of parent/subject), "B" (biography), "C" (unverified), "DD" (conflicting quotes).
  - Categorized life events (career pinnacles, marriages, awards, health challenges) tagged with dates for transit and progression verification.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Ingest curated archetype case studies (AA-rated artists, leaders, scientists) to provide chart-grounded illustrative analogies during user readings.
  - *Chunking Strategy*: Markdown profiles containing natal chart summary + major life transit events.
  - *Metadata Tagging*:
    ```json
    {
      "source": "astro_databank",
      "rodden_rating": "AA",
      "category": "biographical_archetype",
      "sun_sign": "Aries",
      "moon_sign": "Cancer",
      "ascendant": "Libra"
    }
    ```
  - *Query Patterns*: "Historical examples of Moon in 10th house public recognition", "Case studies of Saturn return in 7th house relationships".
- **Licensing & Access**: Free public access for research, personal study, and non-commercial analysis; content copyright Astrodienst AG.

---

## 3. Numerology Systems (Pythagorean, Chaldean & Kabbalistic)

### 3.1 Python Numerology Library & Core Vibration Profiles
- **Source Name**: `numerology` (PyPI) & Numerology-Calculator
- **Verified URLs**:
  - PyPI: [https://pypi.org/project/numerology/](https://pypi.org/project/numerology/)
  - GitHub: [https://github.com/Michael-Sebero/Numerology-Calculator](https://github.com/Michael-Sebero/Numerology-Calculator)
- **Data Type & Format**: Python library, JSON schemas, calculation scripts.
- **Detailed Description**:
  Covers the full Western Pythagorean numerology system based on the alphabet sequence $A=1, B=2, \dots, I=9, J=1 \dots Z=8$. Computes:
  - **Life Path Number**: Derived from full date of birth ($\text{Month} + \text{Day} + \text{Year}$ with iterative digit reduction preserving Master Numbers).
  - **Expression (Destiny) Number**: Derived from full birth name letter vibrations.
  - **Soul Urge (Heart's Desire) Number**: Derived from vowels ($A, E, I, O, U$, and contextual $Y$).
  - **Personality Number**: Derived from consonants.
  - **Master Numbers**: $11$ (The Visionary), $22$ (The Master Builder), $33$ (The Master Teacher).
  - **Karmic Debt Numbers**: $13$ (Discipline), $14$ (Freedom/Temperance), $16$ (Awakening), $19$ (Self-Reliance).
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Comprehensive interpretation chapters for numbers 1 to 9, master numbers 11, 22, 33, and karmic debts 13, 14, 16, 19.
  - *Chunking Strategy*: Dedicated parent document per number; child chunks for Career, Relationships, Shadow Tendencies, and Positive Action Advice.
  - *Metadata Tagging*:
    ```json
    {
      "system": "pythagorean_numerology",
      "number_type": "life_path",
      "number_value": 11,
      "is_master_number": true,
      "positive_framing": true
    }
    ```
  - *Query Patterns*: "What is the meaning of Life Path 11?", "Soul Urge 5 career preferences", "How to overcome Karmic Debt 16 in relationships?"
- **Licensing & Access**: MIT / Open Source.

---

### 3.2 LanderTome Numerology Calculator (Comparative Pythagorean & Chaldean)
- **Source Name**: `numerologyCalculator`
- **Verified URL**: [https://github.com/LanderTome/numerologyCalculator](https://github.com/LanderTome/numerologyCalculator)
- **Data Type & Format**: Go / Python scripts, algorithmic lookup dictionaries.
- **Detailed Description**:
  Implements both Pythagorean and Chaldean sound vibration systems side-by-side. The Chaldean system:
  - Assigns numbers 1 to 8 based on ancient Babylonian/Chaldean phonetic sound frequencies rather than Latin alphabet order:
    - 1: A, I, J, Q, Y
    - 2: B, K, R
    - 3: C, G, L, S
    - 4: D, M, T
    - 5: E, H, N, X
    - 6: U, V, W
    - 7: O, Z
    - 8: F, P
  - *Sacred Number 9*: Number 9 is revered as holy and never assigned to a letter in the Chaldean alphabet map, appearing only as a sum total.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Ingest technical documentation comparing calculation nuances between Pythagorean (birth name / legal name) and Chaldean (current name / familiar name).
  - *Chunking Strategy*: Markdown sections explaining system differences and vibrational resonances.
  - *Metadata Tagging*:
    ```json
    {
      "system": "chaldean_numerology",
      "category": "sound_vibration_table",
      "sacred_rules": "exclude_9_from_letters"
    }
    ```
  - *Query Patterns*: "Why does Chaldean numerology not assign letters to the number 9?", "Difference between Pythagorean and Chaldean name calculations".
- **Licensing & Access**: MIT License.

---

### 3.3 DivineAPI Numerology Data Schemas & Compound Number Table
- **Source Name**: DivineAPI Numerology Schemas
- **Verified URL**: [https://github.com/DivineAPI/numerology-api](https://github.com/DivineAPI/numerology-api)
- **Data Type & Format**: JSON schemas, API response structures, lookup tables.
- **Detailed Description**:
  Provides industry-standard JSON structures for numerological profiling, including:
  - **Cheiro Compound Numbers (10 to 52)**: Esoteric meanings of double-digit compound numbers (e.g. 10: "Wheel of Fortune", 14: "Movement and Challenge", 23: "The Royal Star of the Lion", 24: "Love and Success", 28: "Trust and Contradiction").
  - Planetary correspondences for numbers (1: Sun, 2: Moon, 3: Jupiter, 4: Rahu/Uranus, 5: Mercury, 6: Venus, 7: Ketu/Neptune, 8: Saturn, 9: Mars).
  - Harmonious colors, lucky gemstones, and auspicious days mapped to numerological vibrations (directly matches AstroGuide's `get_numbers_and_stones` tool).
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Ingest compound number meanings (10-52) and planet-stone-colour validation tables.
  - *Chunking Strategy*: Each compound number as a self-contained JSON node ingested into Chroma DB.
  - *Metadata Tagging*:
    ```json
    {
      "system": "chaldean_compound",
      "compound_number": 23,
      "occult_title": "Royal Star of the Lion",
      "ruling_planet": "Mercury",
      "gemstone": "Emerald"
    }
    ```
  - *Query Patterns*: "What is the occult meaning of compound number 23 in Chaldean numerology?", "Which gemstone aligns with birth number 5 and Mercury?"
- **Licensing & Access**: Open API Documentation / JSON schema reference.

---

### 3.4 Python Hebrew Numbers & Kabbalistic Gematria System
- **Source Name**: `python-hebrew-numbers` & Hebrew Gematria Engine
- **Verified URL**: [https://github.com/OriHoch/python-hebrew-numbers](https://github.com/OriHoch/python-hebrew-numbers)
- **Data Type & Format**: Python library, character conversion tables.
- **Detailed Description**:
  Provides bidirectional conversion between Hebrew alphabet characters and their numerical values according to Kabbalistic Gematria:
  - **Standard Gematria (Absolute Value)**: Aleph ($1$) to Yod ($10$), Kaf ($20$) to Tzadi ($90$), Qof ($100$) to Tav ($400$).
  - **Mispar Gadol**: Final letter forms (Sofit) evaluated with elevated values (Khaf Sofit = $500$, Mem Sofit = $600$, Nun Sofit = $700$, Pe Sofit = $800$, Tzadi Sofit = $900$).
  - **Mispar Katan (Reduced Value)**: Modulo-9 reduction mapping Hebrew letters to root numerical vibrations 1 through 9.
  - Esoteric correspondences between Hebrew letters, the 22 paths of the Tree of Life (Sephirot), the 12 zodiac signs, and the 7 classical planets (as documented in the Sefer Yetzirah).
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Ingestion of Sefer Yetzirah astrological letter correspondences and Gematria reduction algorithms.
  - *Chunking Strategy*: Parent chunks by Hebrew letter/path; children chunks for planetary and elemental correspondences.
  - *Metadata Tagging*:
    ```json
    {
      "system": "kabbalistic_gematria",
      "hebrew_letter": "Bet",
      "path_number": 12,
      "planetary_correspondence": "Mercury",
      "tree_of_life": "Kether_Binah"
    }
    ```
  - *Query Patterns*: "Kabbalistic correspondence of Hebrew letter Bet with planet Mercury", "How does Mispar Katan calculate name values?"
- **Licensing & Access**: MIT License.

---

## 4. Vedic Astrology (Jyotish) Nakshatras, Rashis & Dasha Systems

### 4.1 VedAstro Computational Engine & Jyotish Knowledge Base
- **Source Name**: VedAstro
- **Verified URLs**:
  - GitHub Organization: [https://github.com/VedAstro](https://github.com/VedAstro)
  - Core Repository: [https://github.com/VedAstro/VedAstro](https://github.com/VedAstro/VedAstro)
- **Data Type & Format**: C# / Python library (`vedastro`), REST API endpoints, JSON rule libraries.
- **Detailed Description**:
  VedAstro is an open-source, non-profit computational platform for Vedic astrology backed by Swiss Ephemeris calculations. Features:
  - 596+ Vedic astrology calculation functions.
  - **Planetary Yogas**: Algorithmic definitions and narrative explanations for over 200 classic Vedic Yogas (Gajakesari, Pancha Mahapurusha Yogas: Hamsa, Malavya, Ruchaka, Bhadra, Sasa; Budhaditya, Raja Yoga, Dhana Yoga, Kemadruma Yoga).
  - **Shadbala (Six-Fold Planetary Strength)**: Sthana Bala (positional), Dig Bala (directional), Kala Bala (temporal), Cheshta Bala (motional), Naisargika Bala (natural), Drik Bala (aspectual).
  - **Ashtakoota (Guna Milan)**: Complete 36-point compatibility matrix (Varna 1 pt, Vashya 2 pts, Tara 3 pts, Yoni 4 pts, Graha Maitri 5 pts, Gana 6 pts, Bhakoot 7 pts, Nadi 8 pts).
  - **Panchang & Muhurtha**: Tithi, Vara, Nakshatra, Yoga, Karana, Rahu Kalam, Yamaganda, Gulika Kalam.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Extract JSON yoga definitions and Ashtakoota scoring rules into AstroGuide's `data/tables/` and `data/astrology_notes/`.
  - *Chunking Strategy*: Each yoga definition and Guna category chunked into parent-child markdown nodes.
  - *Metadata Tagging*:
    ```json
    {
      "source": "vedastro",
      "system": "jyotish",
      "category": "planetary_yoga",
      "yoga_name": "Gajakesari",
      "planets_involved": ["Jupiter", "Moon"],
      "auspicious": true
    }
    ```
  - *Query Patterns*: "What conditions form Gajakesari Yoga in a birth chart?", "Explain Nadi Dosha and its remedies in Guna Milan", "How is Shadbala strength computed?"
- **Licensing & Access**: MIT License / Open Source.

---

### 4.2 VedicAstro Python Package & Transit Rules
- **Source Name**: VedicAstro
- **Verified URL**: [https://github.com/diliprk/VedicAstro](https://github.com/diliprk/VedicAstro)
- **Data Type & Format**: Python package, JSON lookup tables.
- **Detailed Description**:
  A modular Python package providing calculations for:
  - 27 Nakshatras with 108 Navamsha padas ($3^\circ 20'$ each), ruling deities, and Vimshottari Dasha planetary rulers.
  - **Gochara (Transit) Rules**: Planet house transits counted from the natal Moon sign, delineating favorable houses, unfavorable houses, and Vedha (obstruction) counter-points (directly validates and enriches AstroGuide's `data/tables/gochara_rules.json`).
  - **Vimshottari Dasha System**: 120-year planetary period cycle: Ketu (7 yrs), Venus (20 yrs), Sun (6 yrs), Moon (10 yrs), Mars (7 yrs), Rahu (18 yrs), Jupiter (16 yrs), Saturn (19 yrs), Mercury (17 yrs), with Mahadasha and Antardasha breakdown formulas.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Nakshatra pada tables and Gochara transit interpretation notes.
  - *Chunking Strategy*: Tabular JSON/Markdown nodes per Nakshatra and transit house.
  - *Metadata Tagging*:
    ```json
    {
      "source": "vedicastro",
      "system": "jyotish",
      "category": "transit_gochara",
      "transiting_planet": "Saturn",
      "house_from_moon": 11,
      "is_favourable": true
    }
    ```
  - *Query Patterns*: "Saturn transit in 11th house from natal Moon effect", "Nakshatra pada calculation for Moon at 15 degrees Aries", "Vimshottari dasha sequence and durations".
- **Licensing & Access**: MIT License.

---

### 4.3 Classical Astrological Literature & Scripture Database
- **Source Name**: ASTROLOGY-BOOKS-DATABASE
- **Verified URL**: [https://github.com/ayushman1024/ASTROLOGY-BOOKS-DATABASE](https://github.com/ayushman1024/ASTROLOGY-BOOKS-DATABASE)
- **Data Type & Format**: PDF, Markdown summaries, chart archives.
- **Detailed Description**:
  A curated reference repository of seminal classical astrological literature covering Vedic (Jyotish), Nadi, KP (Krishnamurti Paddhati), and Esoteric traditions. Includes source material and translated commentary from:
  - *Brihat Parashara Hora Shastra (BPHS)*: The foundational scripture of Parashari Jyotish, detailing planetary characters, Karakatwas, divisional charts (D1 Rashi, D9 Navamsha, D10 Dashamsha), and remedial measures.
  - *Jaimini Upadesha Sutras*: Chara Dasha, Karakamsha, and Arudha Padas.
  - *Saravali* of Kalyanavarma: Planetary combinations in signs and Bhavas.
  - *Phaladeepika* of Mantreswara: Transit effects, Dasha interpretation, and Bhavartha Ratnakara principles.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Chapter summaries and translated shlokas converted to clean Markdown for ingestion via Docling.
  - *Chunking Strategy*: Structured parent sections per chapter; child nodes for individual shloka interpretations (`max_chars=800`).
  - *Metadata Tagging*:
    ```json
    {
      "source": "classical_jyotish_database",
      "text": "Brihat_Parashara_Hora_Shastra",
      "topic": "bhava_karakatwa",
      "house": 4,
      "tradition": "parashari"
    }
    ```
  - *Query Patterns*: "Parashara definition of 4th house significations", "Jaimini Chara Dasha calculation rules", "Classical remedies for afflicted Jupiter".
- **Licensing & Access**: Public GitHub Research Collection / Historical texts in public domain.

---

## 5. Open Multi-Disciplinary Datasets (Hugging Face, Kaggle & GitHub)

### 5.1 AmareshHebbar/jyotish-llm-sft (Hugging Face)
- **Source Name**: `jyotish-llm-sft`
- **Verified URL**: [https://huggingface.co/datasets/AmareshHebbar/jyotish-llm-sft](https://huggingface.co/datasets/AmareshHebbar/jyotish-llm-sft)
- **Data Type & Format**: Parquet / JSONL, 1,000,000+ grounded instruction-response rows.
- **Detailed Description**:
  A massive supervised fine-tuning (SFT) and domain knowledge dataset created by Amaresh Hebbar. Covers 8 grounded, citation-tagged sub-collections:
  - Vedic Astrology (Jyotish charts, Dasha analysis, Nakshatras, Yogas)
  - Western Astrology (Natal charts, transits, secondary progressions, house rulerships)
  - Krishnamurti Paddhati (KP astrology, sub-lords, cuspal interlinks)
  - Prashna Kundali (Horary astrology)
  - BaZi (Four Pillars of Destiny)
  - Nine Star Ki & Numerology
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Sample high-value question-answer pairs with citation tags; format into clean Q&A documents for Chroma vector storage.
  - *Chunking Strategy*: Each instruction-response entry ingested as a child chunk with parent category context.
  - *Metadata Tagging*:
    ```json
    {
      "source": "jyotish-llm-sft",
      "tradition": "vedic_western_hybrid",
      "system": "parashari_kp",
      "qa_pair": true,
      "citation_tagged": true
    }
    ```
  - *Query Patterns*: "How does Rahu Mahadasha impact career when placed in 10th house?", "Explaining the sub-lord theory in KP astrology", "Comparison between Western Rising sign and Vedic Lagna".
- **Licensing & Access**: Open access under Apache 2.0 / Creative Commons.

---

### 5.2 Celestial Comprehensive Spiritual AI Dataset (Hugging Face - dp1812)
- **Source Name**: `celestial-comprehensive-spiritual-ai`
- **Verified URL**: [https://huggingface.co/datasets/dp1812/celestial-comprehensive-spiritual-ai](https://huggingface.co/datasets/dp1812/celestial-comprehensive-spiritual-ai)
- **Data Type & Format**: Parquet / JSONL, 9,000+ multi-turn agent interaction examples.
- **Detailed Description**:
  Designed specifically for training and grounding tool-calling AI agents in astrology and numerology. Contains:
  - Multi-turn conversational flows showing how an agent receives birth details, invokes computation tools (birth chart, numerology, daily transits), checks calculation facts, and produces empathetic, constructive narrations.
  - Grounded numerology calculations (Life Path, Expression, Soul Urge) and gemstone/colour recommendations.
  - Uplifting positive action framing examples directly aligning with AstroGuide's `positive_action` output schema requirement.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Use as dynamic few-shot retrieval exemplars in AstroGuide's prompt orchestrator.
  - *Chunking Strategy*: Full multi-turn dialogs ingested with explicit role demarcations.
  - *Metadata Tagging*:
    ```json
    {
      "source": "celestial_spiritual_ai",
      "agent_role": "tool_calling_assistant",
      "features": ["birth_chart", "numerology", "positive_action"],
      "quality": "high_exemplar"
    }
    ```
  - *Query Patterns*: "How should the agent narrate a difficult Saturn transit constructively?", "Example response framing for Life Path 4 user asking about career".
- **Licensing & Access**: Open access on Hugging Face Hub.

---

### 5.3 VedAstro 15,000 Famous People Birth Date Location Dataset (Hugging Face)
- **Source Name**: `15000-Famous-People-Birth-Date-Location`
- **Verified URL**: [https://huggingface.co/datasets/vedastro-org/15000-Famous-People-Birth-Date-Location](https://huggingface.co/datasets/vedastro-org/15000-Famous-People-Birth-Date-Location)
- **Data Type & Format**: Parquet / CSV, 15,000 verified demographic and astrological records.
- **Detailed Description**:
  A benchmark dataset compiled by the VedAstro organization providing verified birth dates, exact birth times, geographical coordinates (latitude, longitude), and accurate historical timezones for 15,000 public figures across history.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Index demographic chart profiles alongside major life achievements for grounding real-world astrological archetypes.
  - *Chunking Strategy*: Tabular records aggregated by Sun, Moon, and Ascendant signs.
  - *Metadata Tagging*:
    ```json
    {
      "source": "vedastro_15k",
      "dataset_type": "empirical_benchmark",
      "sun_sign": "Leo",
      "ascendant": "Scorpio"
    }
    ```
  - *Query Patterns*: "Well-known figures with Sun in Aries and Moon in Sagittarius", "Empirical charts for testing transit calculation engines".
- **Licensing & Access**: Open dataset on Hugging Face.

---

### 5.4 OurNakshatra Vedic Astrology Core Dataset (Hugging Face)
- **Source Name**: `ournakshatra-vedic-astrology-core`
- **Verified URL**: [https://huggingface.co/datasets/OurNakshatra/ournakshatra-vedic-astrology-core](https://huggingface.co/datasets/OurNakshatra/ournakshatra-vedic-astrology-core)
- **Data Type & Format**: JSONL / Parquet, structured Vedic astrology reference nodes.
- **Detailed Description**:
  A focused repository of core Vedic astrological concepts:
  - Deep-dive profiles for all 27 Nakshatras (mythology, symbols, animal totems, Gana, Nadi, Yoni, spiritual purpose).
  - 12 Lagna (Ascendant) comprehensive descriptions in sidereal astrology.
  - Planet-to-deity and planet-to-mantra associations.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Directly populate `data/astrology_notes/` to replace the empty placeholder directory in AstroGuide.
  - *Chunking Strategy*: Markdown articles chunked by Nakshatra and Lagna (`section_merge_max_chars=900`).
  - *Metadata Tagging*:
    ```json
    {
      "source": "ournakshatra_core",
      "topic": "nakshatra_deep_dive",
      "nakshatra_name": "Rohini",
      "ruling_planet": "Moon",
      "element": "Earth"
    }
    ```
  - *Query Patterns*: "Symbolism and deity of Rohini Nakshatra", "Qualities of Mesha (Aries) Lagna in Vedic astrology", "Yoni and Gana classifications for marriage matching".
- **Licensing & Access**: Open access on Hugging Face Hub.

---

### 5.5 ZodiacViews Daily Horoscope Dataset (Hugging Face)
- **Source Name**: `zodiac-horoscope-daily`
- **Verified URL**: [https://huggingface.co/datasets/ZodiacViews/zodiac-horoscope-daily](https://huggingface.co/datasets/ZodiacViews/zodiac-horoscope-daily)
- **Data Type & Format**: JSONL, 5,000+ categorized daily horoscope records.
- **Detailed Description**:
  Structured daily astrological interpretations for all 12 zodiac signs, categorized into General Mood, Love & Relationships, Career & Finance, and Wellness & Growth. Formatted as clean instruction-following examples.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Ingest into Chroma as stylistic reference chunks to enhance the LLM's narration vocabulary during `get_daily_transits` execution.
  - *Chunking Strategy*: 1 record per child chunk, tagged by zodiac sign and life domain.
  - *Metadata Tagging*:
    ```json
    {
      "source": "zodiac_views",
      "sign": "Virgo",
      "domain": "career_finance",
      "tone": "constructive_positive"
    }
    ```
  - *Query Patterns*: "Constructive phrasing for Virgo career daily transit", "Uplifting daily guidance for Gemini Moon".
- **Licensing & Access**: Open access on Hugging Face Hub.

---

### 5.6 Open Astrology Datasets (Kaggle - Gökhan Yu)
- **Source Name**: Open Astrology Datasets
- **Verified URL**: [https://www.kaggle.com/datasets/gokhanyu/open-astrology-datasets](https://www.kaggle.com/datasets/gokhanyu/open-astrology-datasets)
- **Data Type & Format**: CSV files, tabular astrological data.
- **Detailed Description**:
  A collection of normalized CSV datasets covering:
  - Zodiac sign basic properties, ruling planets, natural house correlations, opposing signs, and trine elements.
  - Planetary characteristics (masculine/feminine polarities, natural benefics vs malefics, orbital speeds).
  - Astrological aspect degrees and standard orbs.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Converted to Markdown tables via Docling and ingested into `data/tables/` and Chroma DB.
  - *Chunking Strategy*: Docling native table chunks with summary headers.
  - *Metadata Tagging*:
    ```json
    {
      "source": "kaggle_open_astrology",
      "data_format": "tabular_csv",
      "topic": "zodiac_sign_properties",
      "modality": "Cardinal"
    }
    ```
  - *Query Patterns*: "Which signs form a grand trine with Cancer?", "Polarity and element of Aquarius".
- **Licensing & Access**: Open Database License / CC0 Public Domain.

---

### 5.7 karthiksagarn/astro_horoscope Dataset (Hugging Face)
- **Source Name**: `astro_horoscope`
- **Verified URL**: [https://huggingface.co/datasets/karthiksagarn/astro_horoscope](https://huggingface.co/datasets/karthiksagarn/astro_horoscope)
- **Data Type & Format**: Parquet / JSON, 22,000+ entries.
- **Detailed Description**:
  A large-scale corpus of horoscopic predictions across different signs and dates, useful for training retrieval systems to recognize diverse astrological language and thematic synonyms.
- **Chroma RAG Integration Strategy**:
  - *Ingestion Target*: Used for BM25 lexical vocabulary indexing to ensure high BM25 keyword recall in AstroGuide's hybrid retrieval step.
  - *Chunking Strategy*: Standard section chunks (`max_chars=600`).
  - *Metadata Tagging*:
    ```json
    {
      "source": "karthiksagarn_astro",
      "corpus_type": "lexical_bm25_enhancement",
      "sign": "Libra"
    }
    ```
  - *Query Patterns*: "Thematic variations of Saturn transit in 7th house", "Relationship horoscope themes for Libra".
- **Licensing & Access**: Open access on Hugging Face Hub.

---

## 6. Chroma RAG Integration & Ingestion Architecture

AstroGuide uses an advanced **Corrective RAG (CRAG)** pipeline located in `astroguide/rag/pipeline/`. To maximize retrieval precision and maintain strict adherence to project constraints, the datasets above should be ingested following these architectural specifications:

```
Raw Sources (JSON / Parquet / CSV / MD)
                  │
                  ▼
  [ Docling DocumentConverter / Native JSON Ingestor ]
                  │
                  ├───────────────────────────────┐
                  ▼                               ▼
       Fine-Grained Children Chunks       Parent Sections
         (BM25 + Dense Semantic)       (Expanded LLM Context)
                  │                               │
                  ▼                               │
       Chroma Persistent Client                   │
  (sentence-transformers/all-MiniLM-L6-v2)        │
                  │                               │
                  ▼                               │
      Hybrid RRF + MMR Down-Select                │
                  │                               │
                  ▼                               │
   Cross-Encoder Reranker (top_k = 5)             │
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                     Expanded Parent Context
                                  │
                                  ▼
                   LinUCB Contextual Bandit
              [Direct Gen | Rewrite | Web Search]
                                  │
                                  ▼
                 Agent LLM (Enforced Positivity)
```

### 6.1 Chunking Strategy
- **Parent–Child Hierarchical Chunking**:
  - Fine-grained children chunks ($200$ to $400$ characters) capture specific, high-resolution terms (e.g. `Ketu in Rohini Nakshatra Pada 2`, `Compound Number 23 Royal Star of the Lion`).
  - Upon hybrid retrieval and reranking, the child chunk is expanded to its parent section ($600$ to $900$ characters) stored in `jsonl_output_dir` / `parents_output_dir` so the LLM receives complete context without fragmentation.
- **Section Headers**:
  - Every Markdown chunk must begin with an explicit H2/H3 header (e.g. `## Planet: Jupiter in 9th House`) to enable Docling section boundaries.

### 6.2 Chroma Metadata Schema & Tagging
Chroma metadata fields must adhere to the **3,500-byte limit** per entry (`PipelineConfig.max_metadata_bytes = 3500`). All metadata values must be simple types (`str`, `int`, `float`, `bool`).

Standardized AstroGuide Chroma Metadata Schema:
```json
{
  "doc_id": "doc_vedic_nakshatras_001",
  "chunk_id": "chunk_rohini_pada_2",
  "parent_id": "parent_rohini_overview",
  "tradition": "vedic",
  "category": "nakshatra",
  "primary_entity": "Rohini",
  "secondary_entity": "Moon",
  "house_or_number": 4,
  "sign": "Taurus",
  "positive_action_available": true,
  "source_name": "OurNakshatra_Core",
  "source_url": "https://huggingface.co/datasets/OurNakshatra/ournakshatra-vedic-astrology-core",
  "license": "Apache-2.0"
}
```

### 6.3 Query Patterns & Hybrid Retrieval Mechanics
1. **Lexical BM25 Search**: Matches specific terms, Sanskrit words, and numerical IDs (e.g., `Rohini`, `Shadbala`, `Ashtakoota`, `Gochara`, `Life Path 11`, `Compound 23`).
2. **Dense Semantic Search**: `all-MiniLM-L6-v2` embeds conceptual user questions (e.g., "Why do I feel sudden delays in my career right now?").
3. **Reciprocal Rank Fusion (RRF)**:
   $$\text{RRF\_Score}(d) = \frac{1}{60 + \text{Rank}_{\text{BM25}}(d)} + \frac{1}{60 + \text{Rank}_{\text{Dense}}(d)}$$
4. **Maximal Marginal Relevance (MMR)**: Filter redundant results with diversity parameter $\lambda = 0.7$.
5. **Cross-Encoder Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2` scores the top-5 candidate chunks against the original user query.

---

## 7. Dataset Comparison & Verification Matrix

| # | Source Name | Primary Domain | Data Format | Verified Status | License | Target AstroGuide Feature |
|---|-------------|----------------|-------------|-----------------|---------|---------------------------|
| 1 | **Swiss Ephemeris** | Planetary Ephemeris | Binary `.se1` / C | Verified (200 OK) | GNU GPL v2 / Commercial | `get_birth_chart`, `get_daily_transits` |
| 2 | **pyswisseph** | Python Ephemeris API | C-Extension / Python | Verified (200 OK) | GNU GPL v2 | `astroguide/tools/` deterministic engine |
| 3 | **VSOP87 (VizieR VI/81)** | Planetary Ephemeris | ASCII Tables / Python | Verified (200 OK) | Open Academic (VizieR) | Ephemeris validation & fallback |
| 4 | **Astrology API Benchmark** | Reference Charts | JSON / PyTest | Verified (200 OK) | MIT | Chart calculation accuracy tests |
| 5 | **Kerykeion** | Western Natal & Aspects | Python / JSON / SVG | Verified (200 OK) | AGPL-3.0 | Aspects, orbs & synastry |
| 6 | **Flatlib** | Traditional Dignities | Python / Tables | Verified (200 OK) | MIT | Essential dignities & sects |
| 7 | **AstroGpt** | Signs, Houses, Placements | JSON | Verified (200 OK) | Open Source | RAG planetary descriptions |
| 8 | **Astro-Databank** | Verified Birth Charts | MediaWiki XML | Verified (200 OK) | Non-commercial research | Illustrative archetype case studies |
| 9 | **Python Numerology** | Pythagorean Numerology | Python / JSON | Verified (200 OK) | MIT | `get_numbers_and_stones` (Life Path, Expression) |
| 10 | **LanderTome Calculator** | Chaldean & Pythagorean | Go / Python | Verified (200 OK) | MIT | Sound frequency tables (1-8, no 9) |
| 11 | **DivineAPI Schemas** | Chaldean Compound Numbers | JSON Schemas | Verified (200 OK) | Open Specification | Compound numbers (10-52), stones & colors |
| 12 | **python-hebrew-numbers** | Kabbalistic Gematria | Python | Verified (200 OK) | MIT | Hebrew Gematria & Tree of Life paths |
| 13 | **VedAstro Core** | Vedic Calculations & Yogas | C# / Python / API | Verified (200 OK) | MIT | Yogas, Shadbala, Guna Milan (36 pts) |
| 14 | **VedicAstro** | Gochara & Nakshatras | Python / JSON | Verified (200 OK) | MIT | `data/tables/gochara_rules.json`, padas |
| 15 | **Astrology Books DB** | Classical Texts (BPHS) | Markdown / PDF | Verified (200 OK) | Public Domain / Research | Scriptural authority & shloka grounding |
| 16 | **jyotish-llm-sft (HF)** | Multi-System SFT Corpus | Parquet / JSONL | Verified (200 OK) | Apache 2.0 / CC | High-scale RAG retrieval & QA pairs |
| 17 | **celestial-spiritual-ai (HF)** | Agent Tool-Calling QA | Parquet / JSONL | Verified (200 OK) | Open Access | Few-shot tool-calling & positive framing |
| 18 | **VedAstro 15k Famous (HF)** | Empirical Charts | Parquet / CSV | Verified (200 OK) | Open Access | Statistical grounding & chart validation |
| 19 | **OurNakshatra Core (HF)** | 27 Nakshatras & Lagnas | JSONL / Parquet | Verified (200 OK) | Open Access | Replacing empty `astrology_notes` dir |
| 20 | **ZodiacViews Daily (HF)** | Daily Horoscopes | JSONL | Verified (200 OK) | Open Access | Daily transit narrative phrasing |
| 21 | **Open Astrology (Kaggle)** | Signs & Planetary Props | CSV | Verified (200 OK) | CC0 / ODbL | Tabular sign and element mappings |
| 22 | **astro_horoscope (HF)** | Horoscope Text Corpus | Parquet / JSON | Verified (200 OK) | Open Access | Lexical BM25 vocabulary enhancement |

---

## 8. Licensing, Ethical Guidelines & Disclaimers

### 8.1 Licensing Architecture
- **Permissive Open-Source (MIT / Apache 2.0 / CC0 / ODbL)**:
  `VedAstro`, `VedicAstro`, `flatlib`, `python-hebrew-numbers`, `numerology`, `celestial-comprehensive-spiritual-ai`, `jyotish-llm-sft`, `open-astrology-datasets`. These can be freely embedded, transformed, and distributed within AstroGuide.
- **Copyleft (GNU GPL v2 / AGPL-3.0)**:
  `swisseph`, `pyswisseph`, and `kerykeion`. When distributing integrated binaries under GPL/AGPL, corresponding source code must be made available. For proprietary deployments, commercial licenses are available directly from Astrodienst AG.
- **Research & Non-Commercial Use**:
  `Astro-Databank` is licensed for educational and non-commercial astrological research. Derivative knowledge summaries must cite Astrodienst.

### 8.2 Ethical Guidelines & Enforced Positivity
In accordance with AstroGuide's architectural requirements:
1. **Deterministic Calculation vs LLM Narration**: All mathematical values (degrees, signs, houses, Life Path numbers, Guna Milan scores) must be computed deterministically via code tools and never guessed by the LLM.
2. **Enforced Positivity & Constructive Actions**:
   - Astrological transits labeled as "malefic" or "difficult" (e.g. Saturn square Moon, Rahu Mahadasha, Sade Sati) must always be framed through personal growth, resilience, and constructive remedies.
   - Every reading must conclude with a concrete `positive_action` (e.g. mindful reflection, physical grounding, creative outlet).
3. **Mandatory Guidance & Entertainment Disclaimer**:
   All RAG-augmented responses must adhere to ethical boundaries, noting that astrological guidance is intended for self-reflection and personal inspiration, and does not replace medical, legal, or financial professional counsel.

---
*Authored by worker_m2_1 for AstroGuide Chroma RAG Knowledge Base.*
