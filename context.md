# AstroGuide: Agentic Astrology and Numerology Assistant

## Project Overview
* **Project Name**: AstroGuide[cite: 1]
* **Phase**: Activity 2 - Phase 1 Proposal: Tool-Augmented / Agentic LLM Application[cite: 1]
* **Submission Date**: 19 September 2026[cite: 1]
* **Team Members**:
  * Krishna Menon
  * Aditya Rana
  * Shaksham Mehra

---

## 1. Problem Statement
Most existing astrology applications deliver generic, static horoscopes and lack the capability to answer personalized questions regarding a user's specific birth chart[cite: 1]. AstroGuide is designed as an agentic assistant that calculates an authentic birth chart using user-provided birth details, integrating external computational tools and a domain-specific knowledge base[cite: 1]. 

The system enforces a strict separation between calculation and narration: deterministic code computes all astrological data, while the LLM solely interprets and explains these facts to ensure grounded, testable, and uplifting guidance[cite: 1].

---

## 2. Key Features
* **Birth Horoscope & Charts**: Full birth chart computation accompanied by planetary descriptions[cite: 1].
* **Daily Horoscope**: Transits scored via deterministic rules and narrated by the LLM[cite: 1].
* **Auspicious / Inauspicious Dates**: Uplifting date recommendations that consistently end with an encouraging action[cite: 1].
* **Lucky Indicators**: Personalized lucky number, lucky colour, and gemstone recommendations[cite: 1].
* **Compatibility Testing**: Guna Milan matching based on lunar placements[cite: 1].
* **Chart-Grounded Q&A**: Interactive question answering over the user's computed chart and numbers[cite: 1].
* **Enforced Positivity**: Tone and framing are guaranteed via prompt instructions, a dedicated Pydantic output schema field (`positive_action`), and an explicit tone-check parsing step[cite: 1].

---

## 3. System Architecture & Components
+-----------------------------------------------+
            |                User Interface                 |
            |     Streamlit / Gradio: birth details + chat  |
            +-----------------------+-----------------------+
                                    |
                                    v
+-------------------------------------------------------------------------------+
|                 LangChain Tool-Calling Agent (LCEL + LangGraph)               |
|                                                                               |
|  +-----------------------+     +-------------------+     +------------------+ |
|  |        Memory         | --> |     Agent LLM     | --> | Framing + Parser | |
|  | Chat history + profile|     | Plans, picks, acts|     | Tone check, JSON | |
|  +-----------------------+     +-------------------+     +------------------+ |
+-------+--------------------+------------+---------------+------------+--------+
|                    |            |               |            |
v                    v            v               v            v
+---------------+   +--------------+ +----------+   +-----------+ +-------------+
|  Chart Tool   |   | Numbers Tool | |Match Tool|   |Dates Tool | | RAG Search  |
| Swiss Ephem.  |   | Picks/Stones | |Guna Milan|   |Rules/Tithi| |Chroma: Astro|
+---------------+   +--------------+ +----------+   +-----------+ +-------------+



### Agent Tools Specification
Tools return facts exclusively as structured JSON; the LLM handles narration without hallucinating planetary placements[cite: 1].

| Tool | Feature Covered | Underlying Implementation |
| :--- | :--- | :--- |
| `get_birth_chart` | Birth horoscope; charts with planetary descriptions[cite: 1] | `pyswisseph` (sidereal, Lahiri ayanamsa); `geopy` + `timezonefinder` for location resolution; chart image generator[cite: 1]. |
| `get_daily_transits` | Daily horoscope[cite: 1] | Current planetary transits vs. natal Moon (Gochara principles); scored programmatically and narrated by the LLM[cite: 1]. |
| `get_numbers_and_stones` | Lucky number, colour, gemstone[cite: 1] | Algorithmic numerology functions mapped to planet-to-stone/colour JSON lookup tables[cite: 1]. |
| `match_compatibility` | Compatibility test[cite: 1] | Vedic Ashtakoota / Guna Milan (36-point scale) derived from both partners' Moon nakshatras[cite: 1]. |
| `find_dates` | Good/bad date guidance[cite: 1] | Evaluates Tithi, Chandrabala, Tarabala, and Rahu Kalam; mandates a constructive `positive_action` per date[cite: 1]. |
| `rag_search` | Planetary descriptions; QA over charts & numerology[cite: 1] | Chroma vector database with citations retrieved from curated team astrology notes[cite: 1]. |

---

## 4. LangChain Framework Components
1. **Tool / Agent**: Tool-calling agent implemented with `LangGraph` (`create_react_agent`) managing the 6 specialized tools[cite: 1].
2. **LCEL Composition**: Modular `prompt | LLM | parser` pipelines for generating horoscopes, scoring dates, and executing the tone check[cite: 1].
3. **Memory Management**: `RunnableWithMessageHistory` maintaining conversational turns and caching calculated birth chart JSON within the session state for efficient follow-up reasoning[cite: 1].
4. **Output Parsers**: Structured `Pydantic` schemas enforcing consistent outputs for charts, horoscopes, and positive action framing[cite: 1].
5. **VectorStore Retriever**: `Chroma` utilizing Maximal Marginal Relevance (MMR) retrieval, filtered by metadata (sign, planet, house)[cite: 1].

---

## 5. Team Responsibilities
* **Aditya Rana**: Astrological and numerological calculation tools, geocoding/timezone pipelines, and visual chart rendering[cite: 1].
* **Shaksham Mehra**: Agent orchestration, LangGraph design, session memory, prompt engineering, and the positive framing validation layer[cite: 1].
* **Krishna Menon**: Chroma RAG knowledge base setup, UI implementation (Streamlit/Gradio), evaluation scenarios, and report documentation[cite: 1].

---

## 6. Testing, Edge Cases & Evaluation Plan
* **Evaluation Scenarios (5 Core Tests)**:
  1. Birth chart calculation accuracy verified against established reference calculators[cite: 1].
  2. Daily transit scoring and narrative delivery[cite: 1].
  3. Two-chart compatibility score (Guna Milan 36-point validation)[cite: 1].
  4. Date selection logic and enforcement of the uplifting action requirement[cite: 1].
  5. Chart-grounded conversational QA test[cite: 1].
* **Risk & Failure Handling**:
  * If a birth location is ambiguous or birth time is missing, the agent triggers a conversational clarification request[cite: 1].
  * If the user cannot provide an exact time, it defaults to a standard solar noon chart accompanied by an explicit uncertainty disclaimer[cite: 1].
* **Compliance**: All generated outputs include an entertainment and guidance disclaimer[cite: 1].