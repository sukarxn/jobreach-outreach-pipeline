"""
dashboard_sync.py — POST pipeline results to the deployed web dashboard.

Set DASHBOARD_API_URL in .env to enable.
If not set, this module is a no-op (fails silently).
"""

import os
import json
import urllib.request
import urllib.error
from utils.logger import log


def get_dashboard_url() -> str | None:
    return os.getenv("DASHBOARD_API_URL", "").rstrip("/") or None


def post_jobs(jobs: list[dict]) -> bool:
    """POST a list of job dicts to /api/jobs on the dashboard."""
    url = get_dashboard_url()
    if not url or not jobs:
        return False

    endpoint = f"{url}/api/jobs"
    payload = json.dumps(jobs).encode("utf-8")

    try:
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            log.info(f"Dashboard sync: {result.get('count', '?')} jobs posted to {endpoint}")
            return True
    except urllib.error.HTTPError as e:
        log.warning(f"Dashboard sync HTTP error {e.code}: {e.read().decode()}")
    except Exception as e:
        log.warning(f"Dashboard sync failed (non-critical): {e}")
    return False


def post_run(scraped: int, accepted: int, messages: int, duration: int, error: str = None) -> bool:
    """POST a pipeline run record to /api/runs on the dashboard."""
    url = get_dashboard_url()
    if not url:
        return False

    endpoint = f"{url}/api/runs"
    payload = json.dumps({
        "status": "failed" if error else "completed",
        "jobs_scraped": scraped,
        "jobs_accepted": accepted,
        "messages_generated": messages,
        "duration_seconds": duration,
        "error_message": error,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info(f"Dashboard run logged to {endpoint}")
            return True
    except Exception as e:
        log.warning(f"Dashboard run log failed (non-critical): {e}")
    return False
