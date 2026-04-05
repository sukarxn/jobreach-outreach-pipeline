"""
Streamlit Dashboard — AI Job Outreach Pipeline
Sukaran Gulati

Run: streamlit run dashboard/app.py
"""

import sys
import os
import subprocess
import threading
import queue
import time
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from modules.db import get_all_jobs, update_status, get_jobs_for_export, mark_exported
from utils.csv_exporter import export_to_csv

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="JobReach — Sukaran Gulati",
    page_icon="⚡",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&family=JetBrains+Mono:wght@400&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    /* Dark background */
    .stApp { background-color: #0a0f0a; }
    section[data-testid="stSidebar"] { background-color: #0d150d !important; border-right: 1px solid #1e2e1e; }

    h1, h2, h3 { font-family: 'Syne', sans-serif !important; color: #f0faf0 !important; }

    /* Metrics */
    [data-testid="stMetric"] {
        background: #111a11;
        border: 1px solid #1e2e1e;
        border-radius: 10px;
        padding: 16px !important;
    }
    [data-testid="stMetricValue"] { color: #f0faf0 !important; font-family: 'Syne', sans-serif !important; }
    [data-testid="stMetricLabel"] { color: #6b9b6b !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.08em; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: #111a11; border-radius: 8px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { color: #6b9b6b !important; border-radius: 6px; }
    .stTabs [aria-selected="true"] { background: #1e2e1e !important; color: #22c55e !important; }

    /* Expander */
    .streamlit-expanderHeader {
        background: #111a11 !important;
        border: 1px solid #1e2e1e !important;
        border-radius: 8px !important;
        color: #f0faf0 !important;
        font-size: 13px !important;
    }
    .streamlit-expanderContent {
        background: #0d150d !important;
        border: 1px solid #1e2e1e !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* Buttons */
    .stButton > button {
        background: #22c55e !important;
        color: #0a0f0a !important;
        border: none !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }
    .stButton > button:hover { background: #16a34a !important; }

    /* Text inputs / selects */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background: #111a11 !important;
        color: #f0faf0 !important;
        border: 1px solid #1e2e1e !important;
        border-radius: 8px !important;
    }

    /* Log terminal */
    .log-terminal {
        background: #070c07;
        border: 1px solid #1e2e1e;
        border-radius: 8px;
        padding: 12px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        line-height: 1.7;
        max-height: 320px;
        overflow-y: auto;
        color: #d1fae5;
        white-space: pre-wrap;
        word-break: break-all;
    }

    /* Divider */
    hr { border-color: #1e2e1e !important; }

    /* Multiselect tags */
    [data-baseweb="tag"] { background: #1e2e1e !important; color: #22c55e !important; }

    /* Download button */
    .stDownloadButton > button {
        background: #162016 !important;
        color: #22c55e !important;
        border: 1px solid #1e2e1e !important;
    }
</style>
""", unsafe_allow_html=True)

STATUS_OPTIONS = [
    "pending",
    "message_generated",
    "sent_manually",
    "replied",
    "no_reply",
    "interview",
    "filtered_out",
    "scrape_only",
]

STATUS_EMOJI = {
    "pending":           "⬜ Pending",
    "message_generated": "🔵 Ready",
    "sent_manually":     "🟡 Sent",
    "replied":           "🟢 Replied",
    "no_reply":          "🔴 No Reply",
    "interview":         "🟣 Interview",
    "filtered_out":      "⬛ Filtered",
    "scrape_only":       "⬛ Scrape Only",
}

# ── Pipeline runner ───────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).parent.parent

def _run_pipeline_thread(log_queue: queue.Queue):
    """Run main.py and push lines into log_queue."""
    try:
        proc = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=str(PIPELINE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                log_queue.put(line)
        proc.wait()
        elapsed = ""
        status = "completed ✓" if proc.returncode == 0 else f"failed (exit {proc.returncode})"
        log_queue.put(f"[agent] Pipeline {status}")
    except Exception as e:
        log_queue.put(f"[agent] ERROR: {e}")
    finally:
        log_queue.put("__DONE__")


# ── Data loaders ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_jobs():
    return get_all_jobs(limit=1000)


def compute_metrics(jobs):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_jobs = [j for j in jobs if (j.get("scraped_at") or "").startswith(today)]
    sent    = sum(1 for j in jobs if j.get("message_status") == "sent_manually")
    replied = sum(1 for j in jobs if j.get("message_status") == "replied")
    return {
        "total":         len(jobs),
        "today_scraped": len(today_jobs),
        "generated":     sum(1 for j in jobs if j.get("message_status") == "message_generated"),
        "sent":          sent,
        "replied":       replied,
        "interview":     sum(1 for j in jobs if j.get("message_status") == "interview"),
        "reply_rate":    f"{replied/sent*100:.0f}%" if sent > 0 else "—",
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Session state init
    if "pipeline_logs" not in st.session_state:
        st.session_state.pipeline_logs = []
    if "pipeline_running" not in st.session_state:
        st.session_state.pipeline_running = False
    if "log_queue" not in st.session_state:
        st.session_state.log_queue = None

    # Drain log queue if pipeline is running
    if st.session_state.pipeline_running and st.session_state.log_queue:
        q = st.session_state.log_queue
        new_lines = []
        try:
            while True:
                line = q.get_nowait()
                if line == "__DONE__":
                    st.session_state.pipeline_running = False
                    st.cache_data.clear()
                    break
                new_lines.append(line)
        except queue.Empty:
            pass
        if new_lines:
            st.session_state.pipeline_logs.extend(new_lines)

    # ── Header ────────────────────────────────────────────────────────────────
    col_title, col_run = st.columns([3, 1])
    with col_title:
        st.markdown("<h1 style='margin-bottom:2px'>⚡ JobReach</h1>", unsafe_allow_html=True)
        st.caption(f"Sukaran Gulati · {datetime.now().strftime('%A, %d %B %Y · %H:%M')}")
    with col_run:
        st.markdown("<div style='height:8px'/>", unsafe_allow_html=True)
        if st.session_state.pipeline_running:
            st.button("⏳ Running...", disabled=True, use_container_width=True)
        else:
            if st.button("▶ Run Pipeline Now", use_container_width=True, type="primary"):
                st.session_state.pipeline_logs = ["[agent] Starting pipeline..."]
                st.session_state.pipeline_running = True
                q = queue.Queue()
                st.session_state.log_queue = q
                t = threading.Thread(target=_run_pipeline_thread, args=(q,), daemon=True)
                t.start()
                st.rerun()

    # ── Live log terminal ─────────────────────────────────────────────────────
    if st.session_state.pipeline_logs:
        log_text = "\n".join(st.session_state.pipeline_logs)
        st.markdown(f'<div class="log-terminal">{log_text}</div>', unsafe_allow_html=True)
        if st.session_state.pipeline_running:
            time.sleep(1)
            st.rerun()
        else:
            if st.button("✕ Clear logs"):
                st.session_state.pipeline_logs = []
                st.rerun()

    st.divider()

    # ── Load data ─────────────────────────────────────────────────────────────
    try:
        jobs = load_jobs()
    except Exception as e:
        st.error(f"Supabase connection error: {e}")
        st.info("Check SUPABASE_URL and SUPABASE_KEY in your .env file.")
        return

    m = compute_metrics(jobs)

    # ── Metrics ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Jobs",      m["total"])
    c2.metric("Scraped Today",   m["today_scraped"])
    c3.metric("Messages Ready",  m["generated"])
    c4.metric("Sent Manually",   m["sent"])
    c5.metric("Replied",         m["replied"])
    c6.metric("Interviews",      m["interview"])

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📋 Today's Jobs", "📊 All History", "⚙️ Config & Export"])

    # ── Tab 1: Today ──────────────────────────────────────────────────────────
    with tab1:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_jobs = [j for j in jobs if (j.get("scraped_at") or "").startswith(today)]
        if not today_jobs:
            st.info("No jobs scraped today yet. Click **▶ Run Pipeline Now** above.")
        else:
            st.markdown(f"**{len(today_jobs)} jobs scraped today**")
            _render_jobs(today_jobs, key_prefix="today")

    # ── Tab 2: History ────────────────────────────────────────────────────────
    with tab2:
        st.markdown(f"**{len(jobs)} total jobs**")

        f1, f2, f3 = st.columns(3)
        with f1:
            status_filter = st.multiselect(
                "Status", STATUS_OPTIONS,
                default=["message_generated", "sent_manually", "replied", "interview"],
                key="hist_status",
            )
        with f2:
            companies = sorted({j.get("company_name", "") for j in jobs if j.get("company_name")})
            company_filter = st.multiselect("Company", companies, key="hist_company")
        with f3:
            search = st.text_input("Search", placeholder="title, company, recruiter...", key="hist_search")

        filtered = jobs
        if status_filter:
            filtered = [j for j in filtered if j.get("message_status") in status_filter]
        if company_filter:
            filtered = [j for j in filtered if j.get("company_name") in company_filter]
        if search:
            t = search.lower()
            filtered = [j for j in filtered if
                t in (j.get("job_title") or "").lower() or
                t in (j.get("company_name") or "").lower() or
                t in (j.get("recruiter_name") or "").lower()]

        st.caption(f"{len(filtered)} jobs shown")
        _render_jobs(filtered, key_prefix="hist")

    # ── Tab 3: Config & Export ────────────────────────────────────────────────
    with tab3:
        left, right = st.columns(2)

        with left:
            st.markdown("#### 📥 Export CSV")
            if st.button("Export All Jobs to CSV", type="primary"):
                export_jobs = get_jobs_for_export()
                if export_jobs:
                    csv_path = export_to_csv(export_jobs, label="dashboard")
                    mark_exported([j["id"] for j in export_jobs if j.get("id")])
                    with open(csv_path, "rb") as f:
                        st.download_button(
                            label=f"⬇ Download {Path(csv_path).name}",
                            data=f.read(),
                            file_name=Path(csv_path).name,
                            mime="text/csv",
                        )
                    st.success(f"Exported {len(export_jobs)} jobs")
                else:
                    st.warning("No jobs to export.")

            st.divider()
            st.markdown("#### 📁 Recent Exports")
            export_dir = Path("output/exports")
            if export_dir.exists():
                csvs = sorted(export_dir.glob("*.csv"), reverse=True)[:5]
                for csv in csvs:
                    st.caption(f"📄 {csv.name} ({csv.stat().st_size // 1024} KB)")
            else:
                st.caption("No exports yet.")

        with right:
            st.markdown("#### ⚙️ Config")
            try:
                with open(PIPELINE_DIR / "config.yaml") as f:
                    cfg = yaml.safe_load(f)
                st.json(cfg)
            except Exception as e:
                st.error(f"Could not read config.yaml: {e}")

            st.divider()
            if st.button("🔄 Refresh data"):
                st.cache_data.clear()
                st.rerun()


# ── Jobs renderer ─────────────────────────────────────────────────────────────

def _render_jobs(jobs_list, key_prefix=""):
    if not jobs_list:
        st.info("No jobs to display.")
        return

    for idx, job in enumerate(jobs_list):
        job_id    = job.get("id", "")
        title     = job.get("job_title") or "Untitled Role"
        company   = job.get("company_name") or "—"
        location  = job.get("location") or "—"
        posted    = job.get("posted_at") or "—"
        recruiter = job.get("recruiter_name") or "—"
        rec_title = job.get("recruiter_title") or ""
        rec_li    = job.get("recruiter_linkedin") or ""
        status    = job.get("message_status") or "pending"
        message   = job.get("outreach_message") or ""
        job_url   = job.get("job_url") or ""
        apply_url = job.get("apply_url") or ""

        label = STATUS_EMOJI.get(status, status)
        header = f"**{title}** @ {company} · {location} · `{label}`"

        with st.expander(header, expanded=False):
            c1, c2, c3 = st.columns([2, 2, 1])

            with c1:
                st.markdown(f"**Company:** {company}")
                st.markdown(f"**Location:** {location}")
                st.markdown(f"**Posted:** {posted}")
                if job_url:
                    st.markdown(f"[🔗 View Job]({job_url})")
                if apply_url and apply_url != job_url:
                    st.markdown(f"[📝 Apply]({apply_url})")

            with c2:
                st.markdown(f"**Recruiter:** {recruiter}")
                if rec_title:
                    st.markdown(f"**Title:** {rec_title}")
                if rec_li:
                    st.markdown(f"[👤 LinkedIn]({rec_li})")

            with c3:
                new_status = st.selectbox(
                    "Status",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
                    key=f"sel_{key_prefix}_{job_id}_{idx}",
                )
                if new_status != status:
                    update_status(job_id, new_status)
                    st.cache_data.clear()
                    st.rerun()

            if message:
                st.divider()
                st.markdown("**📨 Outreach Message** — copy and send on LinkedIn:")
                st.text_area(
                    "message",
                    value=message,
                    height=130,
                    key=f"msg_{key_prefix}_{job_id}_{idx}",
                    label_visibility="collapsed",
                )
            else:
                st.caption("_No message generated yet_")


if __name__ == "__main__":
    main()
