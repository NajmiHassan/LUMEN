"""Streamlit interface for the CrewAI research assistant (LUMEN)."""

import os
import traceback
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from crew import run_research_phase
from export_reports import (
    markdown_to_docx_bytes,
    markdown_to_latex,
    overleaf_open_info,
)

_APP_DIR = Path(__file__).resolve().parent
load_dotenv(_APP_DIR / ".env")

_AGENT_ORDER: list[tuple[str, str]] = [
    ("planner", "Planner"),
    ("searcher", "Searcher"),
    ("extractor", "Extractor"),
    ("analyst", "Analyst"),
    ("writer", "Writer"),
]

_CARD_STYLE = {
    "waiting": ("Waiting", "#475569", "#f1f5f9"),
    "running": ("Running…", "#92400e", "#fde68a"),
    "done": ("Done", "#047857", "#a7f3d0"),
    "error": ("Error", "#b91c1c", "#fecaca"),
}

_GROQ_MODEL = "qwen-qwq-32b"
_HF_SPACE_URL = "https://huggingface.co/new-space"


def _validate_env() -> tuple[bool, str]:
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    missing: list[str] = []
    if not groq_key:
        missing.append("GROQ_API_KEY")
    if not tavily_key:
        missing.append("TAVILY_API_KEY")

    if missing:
        return False, f"Missing environment variable(s): {', '.join(missing)}"
    return True, ""


def _init_state() -> None:
    defaults: dict[str, object] = {
        "report": "",
        "last_topic": "",
        "is_running": False,
        "current_agent": "Idle",
        "progress_log": [],
        "error_message": "",
        "research_ui_active": False,
        "pipeline_next_execute": None,
        "pipeline_prior": {},
        "pipeline_topic": "",
        "agent_ui": {key: "waiting" for key, _ in _AGENT_ORDER},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _log_progress(message: str, agent_name: str) -> None:
    st.session_state["current_agent"] = agent_name
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state["progress_log"].append(f"[{timestamp}] {message}")


def _sync_agent_ui_next_phase(phase_next: int) -> None:
    """
    Highlight the agent that is about to run (phase_next in 0..4), or lock all Done (5).

    Before phase_next runs: earlier agents Done, index phase_next Running, later Waiting.

    """

    if phase_next <= 4:
        for i, (key, _label) in enumerate(_AGENT_ORDER):
            if i < phase_next:
                st.session_state["agent_ui"][key] = "done"
            elif i == phase_next:
                st.session_state["agent_ui"][key] = "running"
            else:
                st.session_state["agent_ui"][key] = "waiting"
    elif phase_next == 5:
        for key, _ in _AGENT_ORDER:
            st.session_state["agent_ui"][key] = "done"


def _reset_pipeline(topic: str) -> None:
    st.session_state["pipeline_topic"] = topic.strip()
    st.session_state["pipeline_prior"] = {}
    st.session_state["pipeline_next_execute"] = 0
    st.session_state["research_ui_active"] = True
    st.session_state["is_running"] = True
    st.session_state["error_message"] = ""
    st.session_state["report"] = ""
    st.session_state["progress_log"] = []
    st.session_state["current_agent"] = _AGENT_ORDER[0][1]
    _sync_agent_ui_next_phase(0)


def _active_sidebar_label() -> str:
    if not st.session_state.get("research_ui_active"):
        return str(st.session_state.get("current_agent", "Idle"))
    ne = st.session_state.get("pipeline_next_execute")
    if isinstance(ne, int):
        if st.session_state.get("is_running") and ne <= 4:
            return _AGENT_ORDER[ne][1]
        if ne >= 5:
            return "Completed"
    return str(st.session_state.get("current_agent", "Idle"))


def _run_next_pipeline_step() -> None:
    """Runs one Crew phase per script execution; repeats via st.rerun()."""
    if not st.session_state.get("research_ui_active"):
        return
    ne = st.session_state.get("pipeline_next_execute")
    if not isinstance(ne, int) or ne > 4:
        return

    topic = st.session_state["pipeline_topic"]
    prior = st.session_state["pipeline_prior"]  # mutable dict, update in place
    _, label_human = _AGENT_ORDER[ne]

    try:
        _log_progress(f"{label_human} Agent started.", f"{label_human} Agent")

        with st.spinner(f"{label_human} is researching…"):
            out = run_research_phase(topic, ne, prior)
            st.session_state["pipeline_prior"] = prior  # write back updated prior

        if ne == 4:
            st.session_state["report"] = out.strip()

        ne_done = ne + 1
        st.session_state["pipeline_next_execute"] = ne_done
        _log_progress(f"{label_human} Agent finished.", f"{label_human} Agent")

        if ne_done <= 4:
            _sync_agent_ui_next_phase(ne_done)
            st.session_state["current_agent"] = _AGENT_ORDER[ne_done][1]
            st.rerun()
        else:
            _sync_agent_ui_next_phase(5)
            st.session_state["is_running"] = False
            st.session_state["current_agent"] = "Completed"
            _log_progress("All tasks completed.", "Completed")
            st.rerun()

    except Exception as exc:  # noqa: BLE001
        st.session_state["error_message"] = (
            "Failed during research pipeline. "
            f"Verify API keys and connectivity. Details: {exc}"
        )
        _log_progress(f"{label_human} Agent failed: {exc}", "Error")
        st.session_state["current_agent"] = "Error"
        st.session_state["is_running"] = False

        fail_key = _AGENT_ORDER[ne][0]
        st.session_state["agent_ui"][fail_key] = "error"
        for i in range(ne):
            st.session_state["agent_ui"][_AGENT_ORDER[i][0]] = "done"
        for j in range(ne + 1, len(_AGENT_ORDER)):
            st.session_state["agent_ui"][_AGENT_ORDER[j][0]] = "waiting"
        print(traceback.format_exc())
        st.rerun()


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .lumen-card-inner {
            padding: 0.75rem 1rem;
            border-radius: 12px;
            text-align: center;
            border: 1px solid rgba(0,0,0,0.06);
            min-height: 4.25rem;
        }
        .lumen-card-inner .state { font-size: 0.72rem; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.04em; opacity: 0.9;}
        .lumen-card-inner .title { font-size: 1rem; font-weight: 700; margin-top: 0.3rem;}
        /* Extra top padding so the first line isn’t tight under Streamlit’s header */
        .block-container {
            padding-top: 3rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_agent_progress_panel() -> None:
    st.markdown("##### Agent Progress")
    c1, c2, c3 = st.columns(3)
    c4, c5, spacer = st.columns([1, 1, 2])
    _ = spacer
    cols = [c1, c2, c3, c4, c5]
    for idx, (key, human) in enumerate(_AGENT_ORDER):
        col = cols[idx]
        status = str(st.session_state["agent_ui"].get(key, "waiting"))
        state_text, fg, bg = _CARD_STYLE.get(status, _CARD_STYLE["waiting"])
        with col:
            st.markdown(
                f'<div class="lumen-card-inner" style="background-color:{bg};color:{fg};">'
                f'<div class="state">{state_text}</div>'
                f'<div class="title">{human}</div></div>',
                unsafe_allow_html=True,
            )


def _should_show_agent_progress_panel() -> bool:
    """
    Visible only after a valid Start Research (session flag + pipeline queued).

    Stays visible through running and Done (cursor 5) so the grid shows green.

    Hidden before Start Research (`research_ui_active` is False or cursor None).
    """

    return bool(
        st.session_state.get("research_ui_active")
        and st.session_state.get("pipeline_next_execute") is not None
    )


def main() -> None:
    st.set_page_config(page_title="LUMEN — AI Research Agent", page_icon="◆")
    _init_state()
    _inject_styles()

    with st.sidebar:
        st.markdown("## LUMEN")
        st.caption("Your agentic research buddy!")
        st.markdown(
            "---\n**Note:** Describe your topic thoroughly. After the crew runs, "
            "export **Markdown**, **Word**, **LaTeX**, or publish to Hugging Face."
        )
        st.markdown("---")
        if st.session_state["is_running"]:
            act = _active_sidebar_label()
            st.success(f"Active: **{act}**")
        elif (
            st.session_state.get("research_ui_active")
            and st.session_state.get("pipeline_next_execute") == 5
            and st.session_state.get("report")
        ):
            st.info("Idle — research complete ✓")
        else:
            st.info("Idle")
        model_line = (
            "**Model:** Qwen 2.5 (Groq `"
            + os.getenv("GROQ_MODEL", _GROQ_MODEL)
            + "`)"
        )
        st.markdown(model_line)
        st.markdown("**Search:** Tavily")

    if _should_show_agent_progress_panel():
        nex = int(st.session_state["pipeline_next_execute"])
        _sync_agent_ui_next_phase(min(nex, 5))

    # Plain ASCII apostrophe; native heading avoids brittle markdown/HTML clipping
    st.subheader("Hi! I'm LUMEN — How can I help you today?")
    st.caption(
        "Powered by CrewAI + Qwen · Type your topic below, then click **Start Research** "
        "(pasting alone does not run the agents)."
    )

    _nex = st.session_state.get("pipeline_next_execute")
    if (
        st.session_state.get("research_ui_active")
        and isinstance(_nex, int)
        and _nex <= 4
        and st.session_state.get("is_running")
    ):
        _who = _AGENT_ORDER[_nex][1]
        st.warning(
            f"**Research is running** — the **{_who}** agent is active. "
            "Each phase can take **1–5+ minutes** (Groq + Tavily + CrewAI). "
            "Watch the spinner below and the Agent Progress panel.",
            icon="⏳",
        )

    if "research_topic_field" not in st.session_state:
        st.session_state["research_topic_field"] = (
            str(st.session_state.get("last_topic") or "").strip()
        )

    topic_raw = st.text_input(
        "Research topic",
        label_visibility="collapsed",
        key="research_topic_field",
        placeholder="Enter your research topic…",
    )

    typed = topic_raw.strip() if isinstance(topic_raw, str) else ""

    if st.button(
        "Start Research",
        type="primary",
        disabled=st.session_state["is_running"],
        use_container_width=True,
        key="start_research_btn",
    ):
        if not typed.strip():
            st.warning("Enter a topic, then tap **Start Research**.")
        else:
            valid_env, env_message = _validate_env()
            if not valid_env:
                st.session_state["error_message"] = env_message
            else:
                st.session_state["last_topic"] = typed.strip()
                _reset_pipeline(typed)

    if _should_show_agent_progress_panel():
        with st.container(border=True):
            _render_agent_progress_panel()

    # Run one Crew phase per rerun; spinner here stays near Agent Progress (not at page bottom).
    _run_next_pipeline_step()

    if st.session_state["error_message"]:
        st.error(st.session_state["error_message"])

    _show_log = (
        st.session_state.get("research_ui_active")
        or st.session_state["is_running"]
        or len(st.session_state["progress_log"]) > 0
    )
    if _show_log:
        with st.expander("Activity log", expanded=False):
            if st.session_state["progress_log"]:
                for line in st.session_state["progress_log"]:
                    st.markdown(f"- `{line}`")
            else:
                st.caption("No entries yet.")

    if st.session_state["report"]:
        st.markdown("---")
        st.markdown("### Research report")
        st.markdown(st.session_state["report"])

        report_md = st.session_state["report"]
        latex_src = markdown_to_latex(report_md)
        overleaf_url, overleaf_snip_ok = overleaf_open_info(latex_src)

        st.markdown("###### Export")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.download_button(
                "Download Report (.md)",
                report_md,
                file_name="research_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "Download LaTeX (.tex)",
                latex_src,
                file_name="research_report.tex",
                mime="text/plain",
                use_container_width=True,
            )
        with c3:
            st.download_button(
                "Download Word (.docx)",
                markdown_to_docx_bytes(report_md),
                file_name="research_report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with c4:
            st.link_button(
                "Share to HF Space",
                _HF_SPACE_URL,
                help="Create a Space on Hugging Face to host a demo.",
                use_container_width=True,
            )

        st.link_button("Open in Overleaf", overleaf_url)
        if not overleaf_snip_ok:
            st.info(
                "Large report — download **research_report.tex** and Upload on Overleaf."
            )


if __name__ == "__main__":
    main()
