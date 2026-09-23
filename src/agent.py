"""
agent.py — ReAct agent wired to AstroGuide tools, with conversation memory.

Prerequisites
-------------
Set the ``GOOGLE_API_KEY`` environment variable before importing this module.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from src.tools import get_birth_chart, get_numbers_and_stones
from src.schemas import ChartSummary

# ── LLM ──────────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0)

# ── Agent with memory ────────────────────────────────────────────────────────
memory = MemorySaver()
agent = create_react_agent(
    llm,
    tools=[get_birth_chart, get_numbers_and_stones],
    checkpointer=memory,
)


def ask(question: str, thread_id: str = "demo") -> dict:
    """Send *question* to the agent and return the full result dict.

    Parameters
    ----------
    question : str
        Natural-language question (the agent decides which tools to call).
    thread_id : str
        Conversation thread identifier for memory continuity.

    Returns
    -------
    dict
        The raw LangGraph result containing ``messages`` (including tool_calls).
    """
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [("user", question)]}, config)
    return result


def parse_chart_summary(question: str) -> ChartSummary:
    """Ask the LLM to return a structured ``ChartSummary`` via Pydantic parsing.

    Useful for demonstrating ``with_structured_output`` — pass in a prompt that
    includes birth chart data so the LLM can fill the fields.
    """
    structured_llm = llm.with_structured_output(ChartSummary)
    return structured_llm.invoke(question)

