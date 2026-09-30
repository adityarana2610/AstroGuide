try:
    from langchain_core.tools import tool
except (ImportError, ModuleNotFoundError):
    from astroguide.tools._decorator import tool

from astroguide.tools.birth_chart import get_birth_chart
from astroguide.tools.daily_transits import get_daily_transits
from astroguide.tools.numbers_stones import get_numbers_and_stones
from astroguide.tools.compatibility import match_compatibility
from astroguide.tools.find_dates import find_dates

ALL_TOOLS = [
    get_birth_chart,
    get_daily_transits,
    get_numbers_and_stones,
    match_compatibility,
    find_dates,
]

__all__ = [
    "tool",
    "get_birth_chart",
    "get_daily_transits",
    "get_numbers_and_stones",
    "match_compatibility",
    "find_dates",
    "ALL_TOOLS",
]
