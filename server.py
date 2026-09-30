import sys

# Mock Langchain tools decorator to avoid large dependency
class MockTool:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def invoke(self, args):
        return self.func(**args)

class MockLangchainCoreTools:
    @staticmethod
    def tool(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return MockTool(args[0])
        def wrapper(f):
            return MockTool(f)
        return wrapper

sys.modules['langchain_core'] = type('MockCore', (), {})()
sys.modules['langchain_core.tools'] = MockLangchainCoreTools

import uvicorn
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
import os

from astroguide.tools.birth_chart import get_birth_chart
from astroguide.tools.daily_transits import get_daily_transits
from astroguide.tools.numbers_stones import get_numbers_and_stones
from astroguide.tools.compatibility import match_compatibility
from astroguide.tools.find_dates import find_dates
from astroguide.rag.pipeline import (
    ExternalSearchTool,
    HybridRetriever,
    LinUCBBanditPolicy,
    PipelineConfig,
    SelfHealingRAGAgent,
    DoclingJSONIngestor,
)

app = FastAPI(title="AstroGuide Tools API")

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

_rag_agent = None
_rag_error = None
profile_path = os.path.join(os.path.dirname(__file__), "data", "user_profile.json")
profile_doc_id = "astroguide_user_profile"

ASTROGUIDE_KNOWLEDGE = """AstroGuide knowledge base

Vedic astrology uses the sidereal zodiac and commonly interprets a birth chart through planets, signs, houses, nakshatras, and dashas. A chart is a symbolic framework for reflection; it should not replace medical, legal, financial, or mental-health advice.

The Moon sign describes the sign occupied by the Moon at birth and is often used to discuss emotional patterns, habits, and day-to-day responses. The Moon nakshatra is the lunar mansion occupied by the Moon. There are 27 nakshatras, each divided into four padas.

Gochara, or transit analysis, compares current planetary positions with a natal reference such as the Moon sign. Transit guidance is interpretive and depends on the full chart, timing, and the chosen tradition.

Ashtakoota or Guna Milan is a traditional compatibility framework scored out of 36 points. It compares factors including Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, and Nadi. The score is one interpretive input and should be discussed alongside communication, consent, values, and lived compatibility.

Numerology and gemstone suggestions in AstroGuide are cultural and reflective tools. They are not guarantees of outcomes. Users should verify gemstone quality and consult an appropriately qualified professional before making health or financial decisions.
"""


def empty_profile():
    return {
        "display_name": "",
        "birth_date": "",
        "birth_time": "",
        "birth_location": "",
        "notes": "",
        "charts": [],
    }


def read_profile():
    try:
        with open(profile_path, "r", encoding="utf-8") as profile_file:
            profile = json.load(profile_file)
        return {**empty_profile(), **profile, "charts": profile.get("charts", [])}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return empty_profile()


def write_profile(profile):
    os.makedirs(os.path.dirname(profile_path), exist_ok=True)
    temporary_path = f"{profile_path}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as profile_file:
        json.dump(profile, profile_file, ensure_ascii=True, indent=2, default=str)
    os.replace(temporary_path, profile_path)


def profile_document(profile):
    chart_text = []
    for chart in profile.get("charts", []):
        chart_text.append(
            f"Saved {chart.get('tool', 'tool')} chart on {chart.get('created_at', 'unknown date')}: "
            f"{json.dumps(chart.get('data', {}), ensure_ascii=True, default=str)[:6000]}"
        )
    return "\n\n".join([
        "AstroGuide user profile and saved chart history",
        f"Name: {profile.get('display_name', '')}",
        f"Birth date: {profile.get('birth_date', '')}",
        f"Birth time: {profile.get('birth_time', '')}",
        f"Birth location: {profile.get('birth_location', '')}",
        f"User notes: {profile.get('notes', '')}",
        "Saved charts:",
        "\n".join(chart_text) if chart_text else "No charts saved yet.",
    ])


def index_profile_document(ingestor, profile):
    try:
        ingestor.collection.delete(where={"doc_id": profile_doc_id})
    except Exception:
        pass
    profile_doc = ingestor.parse_document(
        profile_document(profile),
        is_raw_text=True,
        filename="astroguide_user_profile.txt",
    )
    ingestor.ingest_docling_dict(
        profile_doc,
        doc_name="astroguide_user_profile.txt",
        doc_id=profile_doc_id,
    )


def get_rag_agent():
    """Build the RAG pipeline on first use so tool APIs stay lightweight."""
    global _rag_agent, _rag_error
    if _rag_agent is not None:
        return _rag_agent
    if _rag_error is not None:
        raise RuntimeError(_rag_error)

    try:
        config = PipelineConfig()
        ingestor = DoclingJSONIngestor(config=config)
        seeded_doc_id = "astroguide_core_knowledge"
        indexed_ids = {doc["doc_id"] for doc in ingestor.get_indexed_documents()}
        if seeded_doc_id not in indexed_ids:
            seed = ingestor.parse_document(
                ASTROGUIDE_KNOWLEDGE,
                is_raw_text=True,
                filename="astroguide_core_knowledge.txt",
            )
            ingestor.ingest_docling_dict(
                seed,
                doc_name="astroguide_core_knowledge.txt",
                doc_id=seeded_doc_id,
            )
            index_profile_document(ingestor, read_profile())

        retriever = HybridRetriever(ingestor=ingestor, config=config)
        _rag_agent = SelfHealingRAGAgent(
            retriever=retriever,
            bandit_policy=LinUCBBanditPolicy(dimension=config.state_dim, alpha=config.alpha),
            search_tool=ExternalSearchTool(max_results=config.max_search_results),
            config=config,
        )
        return _rag_agent
    except Exception as exc:
        _rag_error = f"RAG initialization failed: {exc}"
        raise RuntimeError(_rag_error) from exc

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

class BirthChartRequest(BaseModel):
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    tz_offset: float
    chart_style: str
    ayanamsha: str = "lahiri"

@app.post("/api/birth_chart")
def api_birth_chart(req: BirthChartRequest):
    try:
        res = get_birth_chart.invoke(req.model_dump())
        if isinstance(res, dict) and "error" in res:
            return {"success": False, "error": res["error"]}
        return {"success": True, "data": res}
    except Exception as e:
        return {"success": False, "error": str(e)}

class NumbersStonesRequest(BaseModel):
    birth_date: str

@app.post("/api/numbers_stones")
def api_numbers_stones(req: NumbersStonesRequest):
    try:
        res = get_numbers_and_stones.invoke(req.model_dump())
        if isinstance(res, dict) and "error" in res:
            return {"success": False, "error": res["error"]}
        return {"success": True, "data": res}
    except Exception as e:
        return {"success": False, "error": str(e)}

class FindDatesRequest(BaseModel):
    natal_moon_sign: int = Field(..., ge=0, le=11)
    natal_nakshatra: int = Field(..., ge=0, le=26)
    start_date: str
    end_date: str
    latitude: float
    longitude: float
    tz_offset: float

@app.post("/api/find_dates")
def api_find_dates(req: FindDatesRequest):
    try:
        res = find_dates.invoke(req.model_dump())
        if isinstance(res, dict) and "error" in res:
            return {"success": False, "error": res["error"]}
        return {"success": True, "data": res}
    except Exception as e:
        return {"success": False, "error": str(e)}

class DailyTransitsRequest(BaseModel):
    natal_moon_sign: int = Field(..., ge=0, le=11)
    natal_moon_degree: float = 0.0
    target_date: Optional[str] = None

@app.post("/api/daily_transits")
def api_daily_transits(req: DailyTransitsRequest):
    try:
        res = get_daily_transits.invoke(req.model_dump())
        if isinstance(res, dict) and "error" in res:
            return {"success": False, "error": res["error"]}
        return {"success": True, "data": res}
    except Exception as e:
        return {"success": False, "error": str(e)}

class CompatibilityRequest(BaseModel):
    person1_moon_nakshatra: int = Field(..., ge=0, le=26)
    person1_moon_pada: int = Field(..., ge=1, le=4)
    person2_moon_nakshatra: int = Field(..., ge=0, le=26)
    person2_moon_pada: int = Field(..., ge=1, le=4)

@app.post("/api/compatibility")
def api_compatibility(req: CompatibilityRequest):
    try:
        res = match_compatibility.invoke(req.model_dump())
        if isinstance(res, dict) and "error" in res:
            return {"success": False, "error": res["error"]}
        return {"success": True, "data": res}
    except Exception as e:
        return {"success": False, "error": str(e)}


class RAGRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
    forced_action: Optional[int] = Field(default=None, ge=0, le=2)


@app.post("/api/rag")
def api_rag(req: RAGRequest):
    try:
        agent = get_rag_agent()
        result = agent.process_query(req.query.strip(), forced_action=req.forced_action)
        return {
            "success": True,
            "data": {
                "response": result["response"],
                "query": result["query"],
                "action_name": result["action_name"],
                "rewritten_query": result["rewritten_query"],
                "retrieved_docs": result["retrieved_docs"],
                "external_search_results": result["external_search_results"],
                "retrieval_metrics": result["retrieval_metrics"],
            },
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


class ProfileRequest(BaseModel):
    display_name: str = Field(default="", max_length=120)
    birth_date: str = Field(default="", max_length=30)
    birth_time: str = Field(default="", max_length=30)
    birth_location: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=5000)


class ChartHistoryRequest(BaseModel):
    tool: str = Field(..., min_length=1, max_length=80)
    data: dict


@app.get("/api/profile")
def api_get_profile():
    return {"success": True, "data": read_profile()}


@app.put("/api/profile")
def api_update_profile(req: ProfileRequest):
    profile = {**read_profile(), **req.model_dump()}
    write_profile(profile)
    if _rag_agent is not None:
        index_profile_document(_rag_agent.retriever.ingestor, profile)
        _rag_agent.retriever.invalidate_bm25()
    return {"success": True, "data": profile}


@app.post("/api/profile/charts")
def api_save_chart(req: ChartHistoryRequest):
    profile = read_profile()
    profile["charts"].append({
        "tool": req.tool,
        "created_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "data": req.data,
    })
    profile["charts"] = profile["charts"][-20:]
    write_profile(profile)
    if _rag_agent is not None:
        index_profile_document(_rag_agent.retriever.ingestor, profile)
        _rag_agent.retriever.invalidate_bm25()
    return {"success": True, "data": profile}

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
