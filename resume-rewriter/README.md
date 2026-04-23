# Resume Bullet Rewriter

Paste a job description + your experience. Get 5-8 tailored resume bullets optimized for that role.

Powered by Claude Opus 4.7 (Anthropic API). Single-page Flask app, no database, no auth. MVP.

## Setup

```bash
cd resume-rewriter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your ANTHROPIC_API_KEY
python app.py
```

Open http://localhost:5000.

## Deploy

**PythonAnywhere / any WSGI host:**

```bash
gunicorn -w 2 -b 0.0.0.0:$PORT app:app
```

Set `ANTHROPIC_API_KEY` in the host's env vars.

## What's next

- Stripe ($7/mo subscription, magic-link auth)
- Save / export bullets (PDF, docx)
- "Tailor for another role" reuse flow
- Rate limiting per IP before auth lands
