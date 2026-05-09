"""Tooling for web research agents."""

from crewai.tools import tool
from tavily import TavilyClient


@tool("tavily_search")
def tavily_search(query: str) -> str:
    """
    Search the web with Tavily and return concise structured results.

    Args:
        query: The search query.

    Returns:
        A formatted string containing titles, urls, and snippets.
    """
    try:
        client = TavilyClient()
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_raw_content=False,
        )
        results = response.get("results", [])
        if not results:
            return "No relevant results were found."

        lines: list[str] = []
        for idx, item in enumerate(results, start=1):
            title = item.get("title", "Untitled")
            url = item.get("url", "N/A")
            content = item.get("content", "No summary available.")
            lines.append(
                f"{idx}. Title: {title}\n"
                f"   URL: {url}\n"
                f"   Summary: {content}"
            )
        return "\n\n".join(lines)
    except Exception as exc:  # noqa: BLE001 - bubble tool-safe message
        return f"Tavily search error: {exc}"
