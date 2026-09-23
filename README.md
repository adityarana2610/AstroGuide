# AstroGuide 🪐

**AI-powered Vedic astrology and Chaldean numerology assistant** — a LangChain
tool-calling agent that computes sidereal birth charts and numerology numbers
on demand.

## Problem Statement

Existing astrology apps are either fully manual or purely LLM-hallucinated.
AstroGuide bridges the gap: real ephemeris calculations (Swiss Ephemeris /
Lahiri ayanamsa) wired as *tools* to a GPT-4o-mini agent, so every number in
the report is computed, not generated.

## Quick Start

```bash
# 1. Clone & install
git clone https://github.com/adityarana2610/AstroGuide.git
cd AstroGuide
pip install -r requirements.txt

# 2. Set your Google API key (never commit this)
export GOOGLE_API_KEY="..."            # Linux / macOS
set GOOGLE_API_KEY=...                 # Windows CMD
$env:GOOGLE_API_KEY="..."              # PowerShell

# 3. Run the demo notebook
jupyter notebook notebooks/phase2_demo.ipynb
```

## Project Structure

```
astroguide/
├── notebooks/phase2_demo.ipynb   # Interactive demo (Colab-friendly)
├── src/
│   ├── geocode.py                # Place → (UTC datetime, lat, lon, tz)
│   ├── ephemeris.py              # Sidereal chart via pyswisseph
│   ├── numerology.py             # Chaldean life path / name / birth numbers
│   ├── tools.py                  # LangChain @tool wrappers
│   ├── schemas.py                # Pydantic models for structured output
│   └── agent.py                  # ReAct agent with MemorySaver
├── data/planet_map.json          # Planet → number/stone/colour/day lookup
├── requirements.txt
└── README.md
```

## Phase 2 Scope

| Feature | Status |
|---------|--------|
| Vedic birth chart (sidereal, Lahiri) | ✅ Working |
| Chaldean numerology (life path, birth #, name #) | ✅ Working |
| LangChain tool-calling agent | ✅ Working |
| Conversation memory (MemorySaver) | ✅ Working |
| Pydantic structured output (`ChartSummary`) | ✅ Working |
| Detailed interpretive report | 🔜 Phase 3 |
| Compatibility analysis | 🔜 Phase 3 |
| PDF/chart export | 🔜 Phase 3 |

## Environment Variable

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google AI API key for Gemini 2.0 Flash |

## How the Demo Works

1. The notebook sends a natural-language question to the agent.
2. The agent autonomously decides which tools to call (`get_birth_chart`,
   `get_numbers_and_stones`, or both).
3. Tool results are real computations — not LLM hallucinations.
4. The raw `messages` trace is printed so you can see the `tool_calls` entries
   as proof.
5. A final cell demonstrates Pydantic-parsed structured output.

## Data Sources & Conventions

- **Ephemeris**: Swiss Ephemeris (`pyswisseph`), sidereal mode, Lahiri ayanamsa.
- **Numerology**: Chaldean letter-value system (no 9 assigned to letters;
  however the digit 9 can still appear as a final reduced number, ruled by Mars).
- **Planet map**: `data/planet_map.json` — verified against the following sources:
  - **Gemstones**: [GemPundit — "Know your Gemstone According to Vedic Astrology"](https://gempundit.com/blog/gemstones-of-vedic-astrology) (all 9 Navaratna stones confirmed).
  - **Number-to-planet**: [Dr. J C Chaudhry — Chaldean Numerology Chart](https://jcchaudhry.com/chaldean-numerology-chart). Numbers 4 and 7 use the **Vedic convention** (Rahu/Ketu) instead of the Western outer planets (Uranus/Neptune).
  - **Colours & days**: Vedic Color Therapy / Navagraha associations (standard references).

## License

MIT
