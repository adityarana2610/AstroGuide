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

app = FastAPI(title="AstroGuide Tools API")

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/health")
def health_check():
    """Health check endpoint — returns 200 OK with service status."""
    return {"status": "ok", "service": "AstroGuide Tools API", "version": "1.0.0"}

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

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
