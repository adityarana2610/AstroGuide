"""
schemas.py — Pydantic models for structured LLM output.
"""

from pydantic import BaseModel


class ChartSummary(BaseModel):
    """Minimal structured summary of a birth chart, used for Pydantic-parsed LLM output."""

    name: str
    moon_sign: str
    ascendant: str
    sun_sign: str
