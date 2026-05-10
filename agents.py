"""Agent definitions for the multi-agent research pipeline."""

from crewai import Agent, LLM

from tools import tavily_search

# Use crewai.LLM instead of langchain_groq.ChatGroq
def get_llm() -> LLM:
    return LLM(
        model="groq/llama-3.3-70b-versatile",
        temperature=0.2,
    )


def planner_agent() -> Agent:
    return Agent(
        role="Research Strategist",
        goal=(
            "Understand the topic deeply and generate 4-5 focused "
            "research questions."
        ),
        backstory=(
            "Expert at breaking down complex topics into structured "
            "research plans."
        ),
        llm=get_llm(),
        verbose=True,
    )


def search_agent() -> Agent:
    return Agent(
        role="Web Researcher",
        goal=(
            "Find the most relevant and credible sources for each "
            "research question."
        ),
        backstory=(
            "Skilled at finding high-quality academic and professional "
            "sources."
        ),
        tools=[tavily_search],
        llm=get_llm(),
        verbose=True,
    )


def extractor_agent() -> Agent:
    return Agent(
        role="Information Extractor",
        goal=(
            "Read each source and extract key facts, data points, "
            "and insights."
        ),
        backstory=(
            "Expert at reading dense content and pulling out what matters."
        ),
        tools=[tavily_search],
        llm=get_llm(),
        verbose=True,
    )


def analyst_agent() -> Agent:
    return Agent(
        role="Research Analyst",
        goal=(
            "Synthesize extracted insights, identify patterns, gaps, "
            "and supporting evidence."
        ),
        backstory=(
            "Senior analyst who connects dots across multiple sources."
        ),
        llm=get_llm(),
        verbose=True,
    )


def writer_agent() -> Agent:
    return Agent(
        role="Research Report Writer",
        goal=(
            "Produce a clean, structured markdown report with proper "
            "citations."
        ),
        backstory=(
            "Professional technical writer who makes complex research "
            "accessible."
        ),
        llm=LLM(
            model="gemini/gemini-3-flash-preview",
            temperature=0.2,
            api_key=os.getenv("GEMINI_API_KEY"),
        ),
        verbose=True,
    )