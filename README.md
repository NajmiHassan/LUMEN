# LUMEN

**LUMEN** is a multi-agent research assistant: you describe a topic, a CrewAI pipeline plans, searches (Tavily), extracts, analyzes, and writes a structured report—with exports to Markdown, Word, LaTeX, and links to Overleaf / Hugging Face.

## Stack

- **Orchestration:** [CrewAI](https://www.crewai.com/) (sequential crew)
- **LLM:** Groq — `qwen-qwq-32b` via LangChain
- **Search:** [Tavily](https://tavily.com/)
- **UI:** [Streamlit](https://streamlit.io/)
- **Python:** 3.10+

## Quick start

```bash
cd research_agent
python -m venv .venv
```

**Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`  
**macOS/Linux:** `source .venv/bin/activate`

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

- `GROQ_API_KEY` — from [Groq Console](https://console.groq.com/)
- `TAVILY_API_KEY` — from [Tavily](https://tavily.com/)

Run the app:

```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`). Enter a topic and click **Start Research**.

## Project layout

```text
research_agent/
├── app.py           # Streamlit UI (LUMEN)
├── crew.py          # Crew assembly & phased runs
├── agents.py        # Agent definitions
├── tasks.py         # Task definitions & context chain
├── tools.py         # Tavily search tool
├── export_reports.py # Word / LaTeX export helpers
├── requirements.txt
├── .env.example     # Copy to `.env` (do not commit `.env`)
└── README.md
```

## Notes

- **Secrets:** Never commit `.env`. Only `.env.example` is tracked.
- **Runtime:** Each pipeline phase can take several minutes (LLM + tools).
- **LaTeX / Overleaf:** Download `.tex` or use **Open in Overleaf** (very large reports may need manual upload).

## License

Use and modify for your project; add a license file if you need a formal OSS license.
