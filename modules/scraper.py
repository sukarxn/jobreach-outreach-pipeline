"""
Scraper module — triggers Apify curious_coder/linkedin-jobs-scraper actor
and returns a flat list of job dicts.
"""

import os
from urllib.parse import urlencode, quote_plus
from dotenv import load_dotenv
from apify_client import ApifyClient
from utils.logger import log
from utils.rate_limiter import random_sleep

load_dotenv()

ACTOR_ID = "curious_coder/linkedin-jobs-scraper"


def build_linkedin_search_urls(job_titles: list, locations: list, posted_within_seconds: int) -> list[str]:
    """
    Build LinkedIn job search URLs for each (title, location) combo.
    f_TPR=r{seconds} filters jobs posted within N seconds.
    """
    urls = []
    for title in job_titles:
        for location in locations:
            params = {
                "keywords": title,
                "location": location,
                "f_TPR": f"r{posted_within_seconds}",
                "f_JT": "I",   # I = Internship employment type on LinkedIn
            }
            base = "https://www.linkedin.com/jobs/search/?"
            url = base + urlencode(params, quote_via=quote_plus)
            urls.append(url)
            log.debug(f"Built URL: {url}")
    log.info(f"Built {len(urls)} search URLs ({len(job_titles)} titles × {len(locations)} locations)")
    return urls


def run_scraper(config: dict) -> list[dict]:
    """
    Trigger the Apify actor for all search URLs and return combined results.
    config keys used: job_titles, locations, posted_within_seconds
    """
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        raise EnvironmentError("APIFY_API_TOKEN not set in .env")

    client = ApifyClient(api_token)

    search_urls = build_linkedin_search_urls(
        job_titles=config["job_titles"],
        locations=config["locations"],
        posted_within_seconds=config.get("posted_within_seconds", 18000),
    )

    all_jobs = []
    seen_ids = set()

    # Split into batches of 5 URLs to avoid huge single actor runs
    batch_size = 5
    batches = [search_urls[i:i+batch_size] for i in range(0, len(search_urls), batch_size)]

    for batch_idx, batch_urls in enumerate(batches):
        log.info(f"Apify batch {batch_idx+1}/{len(batches)} — {len(batch_urls)} URLs")
        try:
            run = client.actor(ACTOR_ID).call(
                run_input={
                    "urls": batch_urls,
                    "count": 25,
                },
                timeout_secs=300,
            )

            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                log.warning(f"Batch {batch_idx+1}: no dataset ID returned")
                continue

            items = list(client.dataset(dataset_id).iterate_items())
            log.info(f"Batch {batch_idx+1}: {len(items)} raw results")

            for item in items:
                job_id = str(item.get("id", ""))
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                all_jobs.append(normalize_job(item))

        except Exception as e:
            log.error(f"Apify batch {batch_idx+1} failed: {e}")

        if batch_idx < len(batches) - 1:
            random_sleep(3, 6)  # between batches

    log.info(f"Scraper total: {len(all_jobs)} unique jobs across all batches")
    return all_jobs


def normalize_job(item: dict) -> dict:
    """Map Apify output fields to our internal schema (must match Supabase columns exactly)."""
    return {
        "id":                str(item.get("id", "")),
        "job_url":           item.get("link", ""),
        "job_title":         item.get("title", ""),
        "company_name":      item.get("companyName", ""),
        "location":          item.get("location", ""),
        "posted_at":         item.get("postedAt", ""),
        "description_text":  item.get("descriptionText", ""),
        "seniority_level":   item.get("seniorityLevel", ""),
        "employment_type":   item.get("employmentType", ""),
        "apply_url":         item.get("applyUrl", "") or item.get("link", ""),
        "recruiter_name":    item.get("jobPosterName", ""),
        "recruiter_title":   item.get("jobPosterTitle", ""),
        "recruiter_photo":   item.get("jobPosterPhoto", ""),
        "recruiter_linkedin":item.get("jobPosterProfileUrl", ""),
        "message_status":    "scraped",
        "notes":             f"applicants: {item.get('applicantsCount', '')}" if item.get("applicantsCount") else None,
    }
