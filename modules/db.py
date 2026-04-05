"""
Supabase DB client + all database operations.
Table: jobs
"""

import os
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from utils.logger import log

load_dotenv()

_client: Optional[Client] = None

SUPABASE_SQL = """
-- Run this once in your Supabase SQL editor to create the jobs table

CREATE TABLE IF NOT EXISTS jobs (
  id                  TEXT PRIMARY KEY,
  job_url             TEXT UNIQUE NOT NULL,
  job_title           TEXT,
  company_name        TEXT,
  location            TEXT,
  posted_at           TEXT,
  description_text    TEXT,
  seniority_level     TEXT,
  employment_type     TEXT,
  apply_url           TEXT,

  recruiter_name      TEXT,
  recruiter_title     TEXT,
  recruiter_photo     TEXT,
  recruiter_linkedin  TEXT,

  outreach_message    TEXT,
  message_status      TEXT DEFAULT 'pending',

  scraped_at          TIMESTAMPTZ DEFAULT NOW(),
  exported_at         TIMESTAMPTZ,
  notes               TEXT
);
"""


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _client = create_client(url, key)
    return _client


def job_exists(job_id: str) -> bool:
    """Return True if job already in DB."""
    try:
        res = get_client().table("jobs").select("id").eq("id", job_id).execute()
        return len(res.data) > 0
    except Exception as e:
        log.error(f"DB job_exists error for {job_id}: {e}")
        return False


def upsert_job(job: dict) -> bool:
    """Insert or update a job record. Returns True on success."""
    try:
        get_client().table("jobs").upsert(job, on_conflict="id").execute()
        return True
    except Exception as e:
        log.error(f"DB upsert_job error for {job.get('id')}: {e}")
        return False


def update_status(job_id: str, status: str, notes: str = None) -> bool:
    """Update message_status (and optionally notes) for a job."""
    try:
        payload = {"message_status": status}
        if notes:
            payload["notes"] = notes
        get_client().table("jobs").update(payload).eq("id", job_id).execute()
        return True
    except Exception as e:
        log.error(f"DB update_status error for {job_id}: {e}")
        return False


def update_outreach(job_id: str, message: str) -> bool:
    """Save generated outreach message and set status to message_generated."""
    try:
        get_client().table("jobs").update({
            "outreach_message": message,
            "message_status": "message_generated",
        }).eq("id", job_id).execute()
        return True
    except Exception as e:
        log.error(f"DB update_outreach error for {job_id}: {e}")
        return False


def get_all_jobs(limit: int = 500) -> list[dict]:
    """Fetch all jobs ordered by scraped_at desc."""
    try:
        res = get_client().table("jobs").select("*").order(
            "scraped_at", desc=True
        ).limit(limit).execute()
        return res.data or []
    except Exception as e:
        log.error(f"DB get_all_jobs error: {e}")
        return []


def get_jobs_for_export() -> list[dict]:
    """Fetch all jobs with message_generated status for CSV export."""
    try:
        res = get_client().table("jobs").select("*").order(
            "scraped_at", desc=True
        ).execute()
        return res.data or []
    except Exception as e:
        log.error(f"DB get_jobs_for_export error: {e}")
        return []


def get_run_count_today() -> int:
    """Count how many jobs were processed (message_generated) today."""
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        res = get_client().table("jobs").select("id", count="exact").gte(
            "scraped_at", f"{today}T00:00:00+00:00"
        ).neq("message_status", "filtered_out").execute()
        return res.count or 0
    except Exception as e:
        log.error(f"DB get_run_count_today error: {e}")
        return 0


def mark_exported(job_ids: list[str]) -> bool:
    """Set exported_at timestamp for a list of job IDs."""
    if not job_ids:
        return True
    try:
        now = datetime.now(timezone.utc).isoformat()
        get_client().table("jobs").update({"exported_at": now}).in_("id", job_ids).execute()
        return True
    except Exception as e:
        log.error(f"DB mark_exported error: {e}")
        return False
