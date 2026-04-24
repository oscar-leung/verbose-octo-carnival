# Cold Email Personalizer

Paste a recipient profile + your pitch. Get a personalized cold email + 3 subject lines you can drop straight into GMass or Apollo.

Flask + Claude Opus 4.7 (adaptive thinking + prompt caching on system prompt). Single-page, no DB, MVP.

## Setup

```bash
cd cold-email-personalizer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # paste your ANTHROPIC_API_KEY
python app.py
```

Runs on http://localhost:5001.

## What's next

- CSV batch mode (recipient per row → personalized email per row, GMass-ready export)
- Reply-rate tracking via UTM-in-subject
- A/B variant generation
