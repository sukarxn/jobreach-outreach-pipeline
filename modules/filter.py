"""
Filter module — deduplication, seniority check, keyword relevance, blocklist.
"""

from modules.db import job_exists
from utils.logger import log


def filter_jobs(raw_jobs: list[dict], config: dict) -> tuple[list[dict], dict]:
    """
    Filter raw jobs list against DB + config rules.

    Returns:
        accepted:  list of jobs that passed all filters
        stats:     dict with counts per filter reason
    """
    seniority_kw = [k.lower() for k in config.get("seniority_keywords", [])]
    senior_excl  = [k.lower() for k in config.get("senior_exclusions", [])]
    blocklist    = [c.lower() for c in config.get("blocklist_companies", [])]
    title_kw     = [t.lower() for t in config.get("job_titles", [])]
    max_count    = config.get("max_applications_per_run", 30)

    accepted = []
    stats = {
        "total":          len(raw_jobs),
        "duplicate":      0,
        "too_senior":     0,
        "no_title_match": 0,
        "blocklisted":    0,
        "no_recruiter":   0,
        "cap_hit":        0,
        "accepted":       0,
    }

    for job in raw_jobs:
        job_id    = job.get("id", "")
        title     = (job.get("job_title") or "").lower()
        company   = (job.get("company_name") or "").lower()
        seniority = (job.get("seniority_level") or "").lower()
        recruiter = (job.get("recruiter_name") or "").strip()

        # 1. Dedup
        if job_id and job_exists(job_id):
            log.debug(f"SKIP duplicate: {job_id} — {job.get('job_title')} @ {job.get('company_name')}")
            stats["duplicate"] += 1
            continue

        # 2. Senior exclusion — skip if title contains a senior-level keyword
        if any(excl in title for excl in senior_excl):
            log.debug(f"SKIP too_senior: {job.get('job_title')}")
            stats["too_senior"] += 1
            job["message_status"] = "filtered_out"
            continue

        # 3. Seniority match — title or seniority_level field must contain intern/junior keyword
        #    If LinkedIn already tags it "Internship" that's fine too
        employment_type = (job.get("employment_type") or "").lower()
        has_seniority = (
            any(kw in title for kw in seniority_kw)
            or any(kw in seniority for kw in seniority_kw)
            or "internship" in employment_type
        )
        if not has_seniority:
            log.debug(f"SKIP no_seniority_match: {job.get('job_title')} [{seniority}]")
            stats["too_senior"] += 1
            job["message_status"] = "filtered_out"
            continue

        # 4. Title keyword relevance — must loosely match one of our target titles
        # Use word-level matching: at least 1 word from config title must be in job title
        target_words = set()
        for t in title_kw:
            target_words.update(t.split())
        if not any(word in title for word in target_words):
            log.debug(f"SKIP no_title_match: {job.get('job_title')}")
            stats["no_title_match"] += 1
            job["message_status"] = "filtered_out"
            continue

        # 5. Blocklist
        if company and any(bl in company for bl in blocklist):
            log.debug(f"SKIP blocklisted: {job.get('company_name')}")
            stats["blocklisted"] += 1
            job["message_status"] = "filtered_out"
            continue

        # 6. Must have a recruiter to message — EXCEPT for Greenhouse jobs
        #    (Greenhouse API never exposes recruiter info; outreach_writer handles the fallback)
        source = job.get("source", "linkedin")
        if not recruiter and source != "greenhouse":
            log.debug(f"SKIP no_recruiter: {job.get('job_title')} @ {job.get('company_name')}")
            stats["no_recruiter"] += 1
            job["message_status"] = "filtered_out"
            continue

        # 7. Cap check
        if len(accepted) >= max_count:
            stats["cap_hit"] += 1
            job["message_status"] = "filtered_out"
            continue

        accepted.append(job)
        stats["accepted"] += 1

    log.info(
        f"Filter results — accepted: {stats['accepted']} | "
        f"duplicate: {stats['duplicate']} | too_senior: {stats['too_senior']} | "
        f"no_title_match: {stats['no_title_match']} | blocklisted: {stats['blocklisted']} | "
        f"no_recruiter: {stats['no_recruiter']} | cap_hit: {stats['cap_hit']}"
    )
    return accepted, stats
