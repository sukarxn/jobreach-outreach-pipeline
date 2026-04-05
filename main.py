#!/usr/bin/env python3
"""
main.py — AI Job Outreach Pipeline Orchestrator
Sukaran Gulati | Intern Job Outreach

Run: python main.py
Schedule: cron at 9am, 2pm, 7pm daily
"""

import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ── utils first (logger must load before modules) ────────────────────────────
from utils.logger import log
from utils.rate_limiter import random_sleep
from utils.csv_exporter import export_to_csv
from utils.dashboard_sync import post_jobs, post_run

# ── modules ──────────────────────────────────────────────────────────────────
from modules.scraper import run_scraper
from modules.filter import filter_jobs
from modules.db import upsert_job, update_outreach, update_status, get_run_count_today
from modules.outreach_writer import generate_outreach_message, extract_resume_summary


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    start_time = datetime.now()
    log.info("=" * 60)
    log.info(f"Pipeline started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    # ── Load config ───────────────────────────────────────────────────────────
    try:
        config = load_config()
        log.info(f"Config loaded — {len(config['job_titles'])} job titles, {len(config['locations'])} locations")
    except Exception as e:
        log.error(f"Failed to load config.yaml: {e}")
        sys.exit(1)

    # ── Resume check ──────────────────────────────────────────────────────────
    resume_path = config.get("master_resume_path", "data/master_resume.md")
    if not Path(resume_path).exists():
        log.warning(f"Resume not found at '{resume_path}'.")
        log.warning("Run: python utils/docx_converter.py your_resume.docx")
        log.warning("Continuing without resume summary — messages will be generic.")
        resume_summary = ""
    else:
        from modules.outreach_writer import extract_resume_summary
        resume_summary = extract_resume_summary(resume_path)
        log.info(f"Resume summary extracted ({len(resume_summary.split())} words)")

    candidate_name = config.get("candidate_name", "Sukaran Gulati")
    claude_model   = config.get("claude_model", "claude-sonnet-4-20250514")
    max_per_run    = config.get("max_applications_per_run", 30)

    # ── Scrape ────────────────────────────────────────────────────────────────
    log.info("STEP 1: Scraping LinkedIn jobs via Apify...")
    try:
        raw_jobs = run_scraper(config)
    except Exception as e:
        log.error(f"Scraper failed: {e}")
        sys.exit(1)

    if not raw_jobs:
        log.warning("No jobs returned from scraper. Exiting.")
        sys.exit(0)

    log.info(f"Scraped {len(raw_jobs)} raw jobs")

    # ── Filter ────────────────────────────────────────────────────────────────
    log.info("STEP 2: Filtering jobs...")
    accepted_jobs, filter_stats = filter_jobs(raw_jobs, config)

    # Upsert all jobs to DB (including filtered-out ones for dedup history)
    log.info("Saving all scraped jobs to DB...")
    for job in raw_jobs:
        upsert_job(job)

    if not accepted_jobs:
        log.warning("No jobs passed filters. Nothing to process.")
        _print_summary(start_time, len(raw_jobs), filter_stats, 0, 0, [])
        sys.exit(0)

    log.info(f"{len(accepted_jobs)} jobs passed filters")

    # ── Generate outreach messages ────────────────────────────────────────────
    log.info(f"STEP 3: Generating outreach messages via Claude ({claude_model})...")

    generated = []
    failed    = 0

    for idx, job in enumerate(accepted_jobs, 1):
        job_id    = job.get("id", "")
        job_title = job.get("job_title", "")
        company   = job.get("company_name", "")

        log.info(f"[{idx}/{len(accepted_jobs)}] {job_title} @ {company}")

        message = generate_outreach_message(
            job=job,
            resume_summary=resume_summary,
            candidate_name=candidate_name,
            model=claude_model,
        )

        if message:
            update_outreach(job_id, message)
            job["outreach_message"] = message
            job["message_status"] = "message_generated"
            generated.append(job)
            log.info(f"  ✓ Message generated for {company}")
        else:
            update_status(job_id, "scrape_only")
            failed += 1
            log.warning(f"  ✗ Message generation failed for {company}")

        # Rate limit between Claude calls
        if idx < len(accepted_jobs):
            random_sleep(2, 5)

    # ── CSV Export ────────────────────────────────────────────────────────────
    log.info("STEP 4: Exporting CSV...")
    from modules.db import get_jobs_for_export, mark_exported
    all_jobs_for_export = get_jobs_for_export()
    csv_path = export_to_csv(all_jobs_for_export, label="outreach")

    if csv_path and all_jobs_for_export:
        export_ids = [j["id"] for j in all_jobs_for_export if j.get("id")]
        mark_exported(export_ids)

    # ── Dashboard Sync ────────────────────────────────────────────────────────
    log.info("STEP 5: Syncing to web dashboard...")
    if generated:
        post_jobs(generated)
    duration = int((datetime.now() - start_time).total_seconds())
    post_run(
        scraped=len(raw_jobs),
        accepted=len(accepted_jobs),
        messages=len(generated),
        duration=duration,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    _print_summary(start_time, len(raw_jobs), filter_stats, len(generated), failed, csv_path)


def _print_summary(start_time, scraped, stats, generated, failed, csv_path):
    elapsed = (datetime.now() - start_time).seconds
    log.info("=" * 60)
    log.info("PIPELINE COMPLETE")
    log.info(f"  Duration     : {elapsed}s")
    log.info(f"  Scraped      : {scraped}")
    log.info(f"  Accepted     : {stats.get('accepted', generated)}")
    log.info(f"  Filtered out : duplicate={stats.get('duplicate',0)} | "
             f"too_senior={stats.get('too_senior',0)} | "
             f"no_match={stats.get('no_title_match',0)} | "
             f"blocklisted={stats.get('blocklisted',0)} | "
             f"no_recruiter={stats.get('no_recruiter',0)}")
    log.info(f"  Messages OK  : {generated}")
    log.info(f"  Messages FAIL: {failed}")
    if csv_path:
        log.info(f"  CSV exported : {csv_path}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
