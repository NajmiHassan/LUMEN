"""Task definitions for sequential research workflow."""

from typing import Any

from crewai import Task

from agents import (
    analyst_agent,
    extractor_agent,
    planner_agent,
    search_agent,
    writer_agent,
)


def get_tasks(topic: str) -> list[Task]:
    """Return all tasks wired in sequence for a given research topic (single Crew)."""
    return _build_task_list(topic, use_task_context=True)


def get_tasks_for_phased_run(topic: str, prior_text: dict[str, str]) -> list[Task]:
    """
    Build the same task chain using prior step outputs as text (for phased kickoffs).

    ``prior_text`` keys: planning, search, extract, analyze — only needed for later phases.
    """
    return _build_task_list(topic, use_task_context=False, prior_text=prior_text)


def _build_task_list(
    topic: str,
    *,
    use_task_context: bool,
    prior_text: dict[str, str] | None = None,
) -> list[Task]:
    prior = prior_text or {}

    planning_task = Task(
        description=(
            "Analyze the user topic and create a structured research plan.\n"
            f"Topic: {topic}\n\n"
            "Generate exactly 4-5 focused research questions that are "
            "specific, answerable, and useful for deep analysis."
        ),
        expected_output=(
            "A numbered list of 4-5 focused research questions in markdown."
        ),
        agent=planner_agent(),
    )

    search_desc = (
        "For each research question from the planning task, find credible "
        "and relevant sources. Include a diverse set of perspectives.\n"
        "Provide sources grouped by question with url and short summary."
    )
    if not use_task_context and prior.get("planning"):
        search_desc = (
            f"Planning output (research questions and plan):\n{prior['planning']}\n\n"
            + search_desc
        )

    search_ctx: list[Any] = [planning_task] if use_task_context else []
    search_task = Task(
        description=search_desc,
        expected_output=(
            "A markdown list grouped by research question containing 3-5 "
            "sources each with URL and concise summary."
        ),
        agent=search_agent(),
        context=search_ctx,
    )

    extract_desc = (
        "Read and extract key facts, quotes, and data points from the "
        "sources gathered in the search task. Preserve source mapping."
    )
    if not use_task_context and prior.get("search"):
        extract_desc = (
            f"Search / sources output:\n{prior['search']}\n\n" + extract_desc
        )

    extract_ctx: list[Any] = [search_task] if use_task_context else []
    extraction_task = Task(
        description=extract_desc,
        expected_output=(
            "A structured markdown extraction grouped by source, including "
            "key insights, quotes, and data points with citations."
        ),
        agent=extractor_agent(),
        context=extract_ctx,
    )

    analyze_desc = (
        "Synthesize extracted information across sources. Identify "
        "patterns, disagreements, evidence strength, and research gaps."
    )
    if not use_task_context and prior.get("extract"):
        analyze_desc = (
            f"Extracted insights:\n{prior['extract']}\n\n" + analyze_desc
        )

    analyze_ctx: list[Any] = [extraction_task] if use_task_context else []
    analysis_task = Task(
        description=analyze_desc,
        expected_output=(
            "A synthesized analysis in markdown with findings, evidence "
            "mapping, and explicit research gaps."
        ),
        agent=analyst_agent(),
        context=analyze_ctx,
    )

    writer_desc = (
        "Using all prior outputs, create the final markdown report.\n"
        "Required format:\n"
        "# Research Report: [Topic]\n"
        "## Executive Summary\n"
        "## Research Questions\n"
        "## Key Findings\n"
        "## Evidence & Supporting Data\n"
        "## Research Gaps\n"
        "## Conclusion\n"
        "## References & Citations\n\n"
        "Ensure references cite source URLs clearly."
    )
    writer_ctx: list[Any]
    if use_task_context:
        writer_ctx = [planning_task, search_task, extraction_task, analysis_task]
    else:
        merged = ""
        if prior.get("planning"):
            merged += f"\n\n## Planning\n{prior['planning']}"
        if prior.get("search"):
            merged += f"\n\n## Sources\n{prior['search']}"
        if prior.get("extract"):
            merged += f"\n\n## Extractions\n{prior['extract']}"
        if prior.get("analyze"):
            merged += f"\n\n## Analysis\n{prior['analyze']}"
        writer_desc = writer_desc + f"\n\nUse this material:{merged}"

        writer_ctx = []

    writer_task = Task(
        description=writer_desc.replace("[Topic]", topic),
        expected_output=(
            "A clean markdown research report that exactly follows the "
            "required section structure and includes citations."
        ),
        agent=writer_agent(),
        context=writer_ctx,
    )

    return [
        planning_task,
        search_task,
        extraction_task,
        analysis_task,
        writer_task,
    ]
