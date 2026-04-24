# SOQ Generator (CalCareers)

Niche tool for CalCareers applicants: paste the SOQ prompts + duty statement + your experience, get STAR/CAR-structured responses that mirror the posting's language.

Flask + Claude Opus 4.7 (adaptive thinking + prompt caching on system prompt). Single-page, no DB, MVP.

## Why this exists

Civil service panels score SOQs against a rubric pulled straight from the duty statement. Strong candidates still lose points when their responses don't mirror the posting's language. This tool does that reliably.

## Setup

```bash
cd soq-generator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # paste your ANTHROPIC_API_KEY
python app.py
```

Runs on http://localhost:5002.

## What's next

- DOCX export (state panels sometimes require .docx upload)
- SOQ length enforcement (some postings cap at 2 pages or 1500 words)
- Multi-posting batch mode (one experience → N postings)
- Rubric-match scoring (estimate which MQs/DQs are weakly covered)
