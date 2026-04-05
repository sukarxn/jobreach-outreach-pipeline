# AI Job Outreach Pipeline

Automated LinkedIn job scraping + personalized outreach message generation for **Sukaran Gulati**.

**What it does:**
- Scrapes LinkedIn intern job postings posted in the **last 5 hours** via Apify
- Filters by role, seniority, and blocklist
- Generates a personalized outreach message per recruiter using Claude
- Saves everything to Supabase + exports a CSV
- Streamlit dashboard to track status

**You send the messages manually** — the pipeline hands you the recruiter's LinkedIn URL and a ready-to-send message.

---

## Prerequisites

- Python 3.11+
- API accounts:
  - [Apify](https://apify.com) — free trial available, $1/1000 results
  - [Anthropic](https://console.anthropic.com) — Claude API
  - [Supabase](https://supabase.com) — free tier works fine

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and fill in your 4 keys:

```
APIFY_API_TOKEN=your_token
ANTHROPIC_API_KEY=your_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key    # Settings → API → service_role
```

### 3. Create Supabase table

Go to your Supabase project → SQL Editor → paste and run:

```sql
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
```

### 4. Convert your resume (one time)

```bash
python utils/docx_converter.py path/to/your_resume.docx
# Output: data/master_resume.md
```

Make sure the file has a **Summary** or **About** section at the top — Claude uses this to personalize messages.

### 5. Edit config.yaml (optional)

Tune job titles, locations, blocklist, or daily cap in `config.yaml`.

---

## Running the Pipeline

### Manual run

```bash
python main.py
```

Output example:
```
09:01:05 | INFO     | Pipeline started at 2025-01-15 09:01:05
09:01:06 | INFO     | Built 20 search URLs (5 titles × 4 locations)
09:01:45 | INFO     | Scraped 87 raw jobs
09:01:46 | INFO     | Filter results — accepted: 23 | duplicate: 12 | too_senior: 31 ...
09:02:30 | INFO     | [1/23] Backend Developer Intern @ Stripe
09:02:30 | INFO     |   ✓ Message generated for Stripe
...
09:04:10 | INFO     | CSV exported: output/exports/outreach_2025-01-15_09-04.csv
09:04:10 | INFO     | Messages OK: 22 | Messages FAIL: 1
```

### Streamlit Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`

---

## Automated Cron Schedule (3× daily, every 5 hours)

```bash
crontab -e
```

Add these 3 lines (replace `/path/to/job-outreach` with your actual path):

```cron
0 9  * * *  cd /path/to/job-outreach && /usr/bin/python3 main.py >> logs/cron.log 2>&1
0 14 * * *  cd /path/to/job-outreach && /usr/bin/python3 main.py >> logs/cron.log 2>&1
0 19 * * *  cd /path/to/job-outreach && /usr/bin/python3 main.py >> logs/cron.log 2>&1
```

- **9:00 AM** — catches overnight + early morning posts
- **2:00 PM** — catches mid-day posts
- **7:00 PM** — catches afternoon posts

Each run uses `f_TPR=r18000` (last 18,000 seconds = 5 hours) so runs don't overlap.

To find your Python path: `which python3`

---

## Cost Estimates

| Service | Cost |
|---|---|
| Apify | ~$0.001 per job result ($1/1000) |
| Claude Sonnet | ~$0.003 per message (~300 tokens out) |
| 20 messages/day | ~$0.08/day, ~$2.40/month |
| Supabase | Free tier (500MB, 50K rows) |

---

## Folder Structure

```
job-outreach/
├── main.py                    # Run this
├── config.yaml                # Edit job titles, locations, blocklist
├── .env                       # Your API keys
├── requirements.txt
│
├── data/
│   └── master_resume.md       # Your resume (auto-generated from .docx)
│
├── modules/
│   ├── scraper.py             # Apify LinkedIn scraper
│   ├── filter.py              # Dedup + filtering logic
│   ├── outreach_writer.py     # Claude message generation
│   └── db.py                  # Supabase operations
│
├── dashboard/
│   └── app.py                 # Streamlit UI
│
├── utils/
│   ├── docx_converter.py      # One-time .docx → .md
│   ├── csv_exporter.py        # CSV export
│   ├── rate_limiter.py        # API rate limiting
│   └── logger.py              # Logging setup
│
├── output/exports/            # Generated CSVs
└── logs/                      # Pipeline logs
```

---

## Troubleshooting

**"No jobs returned from scraper"**
- Check your Apify token is valid
- The actor may take 2–5 mins to run — check Apify dashboard for run status
- Verify the LinkedIn search URLs return results manually in a browser

**"Resume not found"**
- Run: `python utils/docx_converter.py your_resume.docx`
- Messages still generate without resume, just less personalized

**Supabase connection error**
- Use the **service_role** key, not the anon key
- Check your Supabase project isn't paused (free tier pauses after 1 week of inactivity)

**Too many "filtered_out" jobs**
- Edit `config.yaml` — loosen `seniority_keywords` or remove items from `senior_exclusions`
- Check `logs/pipeline_*.log` for exact filter reasons
