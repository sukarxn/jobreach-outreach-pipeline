"""
Greenhouse scraper — hits the public Greenhouse Jobs Board API (no API key required).

API: GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

Returns a flat list of normalized job dicts matching the same schema as scraper.py.
"""

import re
import urllib.request
import urllib.error
import json
from datetime import datetime, timezone, timedelta
from utils.logger import log


def _strip_html(html: str) -> str:
    """Unescape HTML entities, strip tags, and normalize whitespace."""
    if not html:
        return ""
    # Step 1: unescape HTML entities first (content field is double-encoded)
    text = re.sub(r"&lt;", "<", html)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    # Step 2: strip all HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Step 3: normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fetch_jobs(board_token: str) -> list[dict]:
    """Fetch all jobs for a Greenhouse board token. Returns raw API response list."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("jobs", [])
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log.warning(f"Greenhouse: board '{board_token}' not found (404) — skipping")
        else:
            log.error(f"Greenhouse: HTTP {e.code} for board '{board_token}'")
        return []
    except Exception as e:
        log.error(f"Greenhouse: failed to fetch board '{board_token}': {e}")
        return []


def _get_company_name(board_token: str) -> str:
    """Fetch the company name from the Greenhouse board metadata."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("name", board_token)
    except Exception:
        # Fall back to capitalizing the token
        return board_token.replace("-", " ").replace("_", " ").title()


def _is_recent(updated_at: str, within_seconds: int) -> bool:
    """Return True if updated_at timestamp is within the last N seconds."""
    if not updated_at:
        return True  # can't determine — include it
    try:
        # Greenhouse uses ISO 8601: "2025-04-07T10:30:00.000Z"
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
        return dt >= cutoff
    except Exception:
        return True  # can't parse — include it


def normalize_greenhouse_job(item: dict, company_name: str) -> dict:
    """Map Greenhouse API fields to our internal job schema."""
    job_id   = item.get("id", "")
    location = item.get("location", {})
    depts    = item.get("departments", [])
    dept     = depts[0].get("name", "") if depts else ""

    return {
        "id":                f"gh_{job_id}",
        "job_url":           item.get("absolute_url", ""),
        "job_title":         item.get("title", ""),
        "company_name":      company_name,
        "location":          location.get("name", "") if isinstance(location, dict) else str(location),
        "posted_at":         item.get("updated_at", ""),
        "description_text":  _strip_html(item.get("content", "")),
        "seniority_level":   "",        # not available in Greenhouse API
        "employment_type":   "",        # not available in Greenhouse API
        "apply_url":         item.get("absolute_url", ""),
        "recruiter_name":    "",        # NOT exposed by Greenhouse API
        "recruiter_title":   "",
        "recruiter_photo":   "",
        "recruiter_linkedin": "",
        "message_status":    "scraped",
        "source":            "greenhouse",
        "notes":             f"dept: {dept}" if dept else None,
    }


def run_greenhouse_scraper(config: dict) -> list[dict]:
    """
    Scrape all configured Greenhouse boards and return a flat list of job dicts.
    config keys used: greenhouse_companies, posted_within_seconds
    """
    board_tokens   = config.get("greenhouse_companies", [])
    within_seconds = config.get("posted_within_seconds", 18000)

    if not board_tokens:
        log.info("Greenhouse: no board tokens configured — skipping")
        return []

    all_jobs  = []
    seen_urls = set()

    for token in board_tokens:
        token = token.strip()
        log.info(f"Greenhouse: fetching board '{token}'...")

        company_name = _get_company_name(token)
        raw_jobs     = _fetch_jobs(token)

        if not raw_jobs:
            log.info(f"Greenhouse: '{token}' — 0 jobs returned")
            continue

        log.debug(f"Greenhouse: '{token}' ({company_name}) — {len(raw_jobs)} total jobs before time filter")

        added = 0
        for item in raw_jobs:
            updated_at = item.get("updated_at", "")

            # Time filter — only jobs updated within our window
            if not _is_recent(updated_at, within_seconds):
                continue

            job_url = item.get("absolute_url", "")
            if not job_url or job_url in seen_urls:
                continue

            seen_urls.add(job_url)
            all_jobs.append(normalize_greenhouse_job(item, company_name))
            added += 1

        log.info(f"Greenhouse: '{token}' ({company_name}) — {added} jobs within time window")

    log.info(f"Greenhouse total: {len(all_jobs)} unique jobs across {len(board_tokens)} boards")
    return all_jobs
