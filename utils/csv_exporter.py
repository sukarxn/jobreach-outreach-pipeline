import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.logger import log


EXPORT_COLUMNS = [
    "id",
    "job_title",
    "company_name",
    "location",
    "posted_at",
    "job_url",
    "apply_url",
    "recruiter_name",
    "recruiter_title",
    "recruiter_linkedin",
    "outreach_message",
    "message_status",
    "scraped_at",
    "notes",
]


def export_to_csv(jobs: list[dict], label: str = "") -> str:
    """
    Export job list to a timestamped CSV.
    Returns the file path.
    """
    Path("output/exports").mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    suffix = f"_{label}" if label else ""
    filename = f"output/exports/outreach_{date_str}{suffix}.csv"

    if not jobs:
        log.warning("No jobs to export.")
        return ""

    # Only keep columns that exist
    df = pd.DataFrame(jobs)
    cols = [c for c in EXPORT_COLUMNS if c in df.columns]
    df = df[cols]

    df.to_csv(filename, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compat
    log.info(f"CSV exported: {filename} ({len(df)} rows)")
    return filename
