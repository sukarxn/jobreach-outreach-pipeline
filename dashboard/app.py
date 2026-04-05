"""
Streamlit Dashboard — AI Job Outreach Pipeline
Sukaran Gulati

Run: streamlit run dashboard/app.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
import pandas as pd

# Add project root to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from modules.db import get_all_jobs, update_status, get_jobs_for_export, mark_exported
from utils.csv_exporter import export_to_csv

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Outreach — Sukaran Gulati",
    page_icon="🚀",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
    }
    .status-badge {
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    div[data-testid="stDataFrame"] table {font-size: 13px;}
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

STATUS_COLORS = {
    "pending":           "#6c757d",
    "message_generated": "#0d6efd",
    "sent_manually":     "#fd7e14",
    "replied":           "#198754",
    "no_reply":          "#dc3545",
    "interview":         "#6f42c1",
    "filtered_out":      "#adb5bd",
    "scrape_only":       "#adb5bd",
}


@st.cache_data(ttl=30)
def load_jobs():
    return get_all_jobs(limit=1000)


def compute_metrics(jobs: list[dict]) -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_jobs = [j for j in jobs if (j.get("scraped_at") or "").startswith(today)]
    total       = len(jobs)
    generated   = sum(1 for j in jobs if j.get("message_status") == "message_generated")
    sent        = sum(1 for j in jobs if j.get("message_status") == "sent_manually")
    replied     = sum(1 for j in jobs if j.get("message_status") == "replied")
    interview   = sum(1 for j in jobs if j.get("message_status") == "interview")
    reply_rate  = f"{(replied / sent * 100):.0f}%" if sent > 0 else "—"
    return {
        "total": total,
        "today_scraped": len(today_jobs),
        "generated": generated,
        "sent": sent,
        "replied": replied,
        "interview": interview,
        "reply_rate": reply_rate,
    }


def main():
    st.title("🚀 Job Outreach Dashboard")
    st.caption(f"Sukaran Gulati — Last refreshed: {datetime.now().strftime('%H:%M:%S')}")

    # Load data
    try:
        jobs = load_jobs()
    except Exception as e:
        st.error(f"Could not connect to Supabase: {e}")
        st.info("Make sure your .env file has SUPABASE_URL and SUPABASE_KEY set.")
        return

    metrics = compute_metrics(jobs)

    # ── Top metrics ──────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Jobs", metrics["total"])
    c2.metric("Scraped Today", metrics["today_scraped"])
    c3.metric("Messages Ready", metrics["generated"])
    c4.metric("Sent Manually", metrics["sent"])
    c5.metric("Replied", metrics["replied"])
    c6.metric("Interviews", metrics["interview"])

    st.divider()

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📋 Today's Jobs", "📊 All History", "⚙️ Config & Export"])

    # ─── TAB 1: Today's Jobs ─────────────────────────────────────────────────
    with tab1:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_jobs = [j for j in jobs if (j.get("scraped_at") or "").startswith(today)]

        if not today_jobs:
            st.info("No jobs scraped today yet. Run `python main.py` to start the pipeline.")
        else:
            st.subheader(f"{len(today_jobs)} jobs scraped today")
            _render_jobs_table(today_jobs, key_prefix="today")

    # ─── TAB 2: All History ───────────────────────────────────────────────────
    with tab2:
        st.subheader(f"All Outreach — {len(jobs)} total")

        # Filters
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            status_filter = st.multiselect(
                "Status", STATUS_OPTIONS,
                default=["message_generated", "sent_manually", "replied", "interview"]
            )
        with col_f2:
            companies = sorted(set(j.get("company_name", "") for j in jobs if j.get("company_name")))
            company_filter = st.multiselect("Company", companies)
        with col_f3:
            search_term = st.text_input("Search title / recruiter", placeholder="e.g. Backend, Google...")

        filtered = jobs
        if status_filter:
            filtered = [j for j in filtered if j.get("message_status") in status_filter]
        if company_filter:
            filtered = [j for j in filtered if j.get("company_name") in company_filter]
        if search_term:
            term = search_term.lower()
            filtered = [j for j in filtered if
                        term in (j.get("job_title") or "").lower() or
                        term in (j.get("recruiter_name") or "").lower() or
                        term in (j.get("company_name") or "").lower()]

        st.caption(f"Showing {len(filtered)} jobs")
        _render_jobs_table(filtered, key_prefix="history")

    # ─── TAB 3: Config & Export ───────────────────────────────────────────────
    with tab3:
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📥 Export CSV")
            if st.button("Export All Jobs to CSV", type="primary"):
                export_jobs = get_jobs_for_export()
                if export_jobs:
                    csv_path = export_to_csv(export_jobs, label="dashboard")
                    mark_exported([j["id"] for j in export_jobs if j.get("id")])
                    # Read and offer download
                    with open(csv_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Download {Path(csv_path).name}",
                            data=f.read(),
                            file_name=Path(csv_path).name,
                            mime="text/csv",
                        )
                    st.success(f"Exported {len(export_jobs)} jobs")
                else:
                    st.warning("No jobs to export.")

            st.divider()
            st.subheader("📁 Recent Exports")
            export_dir = Path("output/exports")
            if export_dir.exists():
                csvs = sorted(export_dir.glob("*.csv"), reverse=True)[:5]
                if csvs:
                    for csv in csvs:
                        size_kb = csv.stat().st_size // 1024
                        st.text(f"📄 {csv.name} ({size_kb} KB)")
                else:
                    st.text("No exports yet.")

        with col_right:
            st.subheader("⚙️ Current Config")
            try:
                import yaml
                with open("config.yaml") as f:
                    cfg = yaml.safe_load(f)
                st.json(cfg)
            except Exception as e:
                st.error(f"Could not read config.yaml: {e}")

            st.divider()
            st.subheader("🔄 Refresh")
            if st.button("Clear cache & refresh data"):
                st.cache_data.clear()
                st.rerun()


def _render_jobs_table(jobs_list: list[dict], key_prefix: str = ""):
    """Render an interactive jobs table with status editor and message expander."""
    if not jobs_list:
        st.info("No jobs to display.")
        return

    for idx, job in enumerate(jobs_list):
        job_id    = job.get("id", "")
        title     = job.get("job_title", "—")
        company   = job.get("company_name", "—")
        location  = job.get("location", "—")
        posted    = job.get("posted_at", "—")
        recruiter = job.get("recruiter_name", "—")
        rec_title = job.get("recruiter_title", "")
        rec_li    = job.get("recruiter_linkedin", "")
        status    = job.get("message_status", "pending")
        message   = job.get("outreach_message", "")
        job_url   = job.get("job_url", "")
        apply_url = job.get("apply_url", "")

        color = STATUS_COLORS.get(status, "#6c757d")

        with st.expander(f"**{title}** @ {company}  —  {location}  `{status}`", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown(f"**Company:** {company}")
                st.markdown(f"**Location:** {location}")
                st.markdown(f"**Posted:** {posted}")
                if job_url:
                    st.markdown(f"[🔗 View Job]({job_url})")
                if apply_url and apply_url != job_url:
                    st.markdown(f"[📝 Apply Here]({apply_url})")

            with col2:
                st.markdown(f"**Recruiter:** {recruiter}")
                if rec_title:
                    st.markdown(f"**Title:** {rec_title}")
                if rec_li:
                    st.markdown(f"[👤 LinkedIn Profile]({rec_li})")

            with col3:
                new_status = st.selectbox(
                    "Update Status",
                    STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0,
                    key=f"{key_prefix}_{job_id}_{idx}",
                )
                if new_status != status:
                    if update_status(job_id, new_status):
                        st.success(f"Updated to {new_status}")
                        st.cache_data.clear()
                        st.rerun()

            # Outreach message
            if message:
                st.divider()
                st.markdown("**📨 Outreach Message:**")
                st.text_area(
                    label="Copy this message",
                    value=message,
                    height=130,
                    key=f"msg_{key_prefix}_{job_id}_{idx}",
                    label_visibility="collapsed",
                )
            else:
                st.caption("_No message generated yet_")


if __name__ == "__main__":
    main()
