"""Crew assembly and execution helpers."""

from pathlib import Path

from crewai import Crew, Process
from dotenv import load_dotenv

from tasks import get_tasks, get_tasks_for_phased_run

load_dotenv(Path(__file__).resolve().parent / ".env")

_PRIOR_KEYS = ("planning", "search", "extract", "analyze")


def run_research(topic: str) -> str:
    """
    Build and run the research crew sequentially (single kickoff).
    """
    tasks = get_tasks(topic)
    crew = Crew(
        agents=[task.agent for task in tasks],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)


def run_research_phase(topic: str, phase_index: int, prior: dict[str, str]) -> str:
    """
    Run one pipeline phase (0=planner … 4=writer) for Streamlit stepwise UI.

    ``prior`` stores string outputs for keys: planning, search, extract, analyze
    as previous phases complete.
    """
    tasks = get_tasks_for_phased_run(topic, prior)
    task = tasks[phase_index]
    crew = Crew(
        agents=[task.agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    out = crew.kickoff()
    result = str(out)
    if phase_index < len(_PRIOR_KEYS):
        prior[_PRIOR_KEYS[phase_index]] = result
    return result
