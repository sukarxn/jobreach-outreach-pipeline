"""
Outreach writer — generates personalized LinkedIn DM / email via Claude.
"""

import os
from dotenv import load_dotenv
import anthropic
from utils.logger import log
from utils.rate_limiter import random_sleep

load_dotenv()

_client = None


def get_anthropic_client():
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set in .env")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


SYSTEM_PROMPT = """You are writing a short, genuine outreach message from an internship seeker to a recruiter or hiring manager on LinkedIn or via email.

The message must be:
- Under 100 words
- Specific to the role and company (use the exact job title and company name)
- Non-generic — absolutely no "I hope this message finds you well", no buzzwords like "passionate", "synergy", "leverage"
- Human, warm, and direct — like a real person wrote it
- End with a soft call-to-action (e.g. "Happy to share my resume if helpful." or "Would love to connect.")

Return ONLY the message text. No subject line. No greeting like "Dear". Start directly with a hook sentence."""


def generate_outreach_message(job: dict, resume_summary: str, candidate_name: str, model: str) -> str | None:
    """
    Generate a personalized outreach message for one job.
    Returns the message string or None on failure.
    """
    recruiter_name  = (job.get("recruiter_name") or "").strip()
    recruiter_title = job.get("recruiter_title") or "Recruiter"
    company_name    = job.get("company_name") or "your company"
    job_title       = job.get("job_title") or "the internship role"
    location        = job.get("location") or "the listed location"
    source          = job.get("source", "linkedin")

    # Greenhouse jobs never have a recruiter — address the hiring team generically
    if not recruiter_name:
        addressee    = f"{company_name} Hiring Team"
        recruiter_line = f"Recipient: {company_name} Hiring Team (no specific recruiter — address generically as 'Hi {company_name} Team,')"
    else:
        addressee    = recruiter_name
        recruiter_line = f"Recruiter: {recruiter_name} ({recruiter_title})"

    user_prompt = f"""{recruiter_line}
Company: {company_name}
Role: {job_title}
Location: {location}
Candidate: {candidate_name}
Source: {source}

Candidate background (brief resume summary):
{resume_summary}

Write an outreach message from {candidate_name} to {addressee} for this specific internship role."""

    try:
        client = get_anthropic_client()
        response = client.messages.create(
            model=model,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        message = response.content[0].text.strip()
        log.debug(f"Message generated for {job_title} @ {company_name} ({len(message.split())} words)")
        return message

    except Exception as e:
        log.error(f"Claude error for {job_title} @ {company_name}: {e}")
        return None


def extract_resume_summary(resume_path: str, max_lines: int = 8) -> str:
    """
    Extract the top summary/intro section from the master resume markdown.
    Looks for a 'Summary' or 'About' section, else takes the first N non-empty lines.
    """
    from pathlib import Path

    path = Path(resume_path)
    if not path.exists():
        log.warning(f"Resume not found at {resume_path} — using empty summary")
        return ""

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Try to find Summary / About / Profile section
    summary_lines = []
    in_summary = False
    for line in lines:
        lower = line.lower().strip()
        if any(kw in lower for kw in ["# summary", "## summary", "# about", "## about", "# profile", "## profile", "# objective"]):
            in_summary = True
            continue
        if in_summary:
            if line.startswith("#"):  # hit next section
                break
            if line.strip():
                summary_lines.append(line.strip())
            if len(summary_lines) >= max_lines:
                break

    if summary_lines:
        return "\n".join(summary_lines)

    # Fallback: first N non-empty, non-heading lines
    fallback = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            fallback.append(stripped)
        if len(fallback) >= max_lines:
            break
    return "\n".join(fallback)
