# SOQ Generator (CalCareers)

Niche tool for CalCareers applicants: paste the SOQ prompts + duty statement + your experience, get STAR/CAR-structured responses that mirror the posting's language.

- **Claude Opus 4.7** with adaptive thinking + prompt caching on the system prompt
- **Structured outputs** (`output_config.format` with a JSON schema)
- **Free tier**: 1 SOQ generation per IP per 24h (each generation can produce N responses)
- **Pro tier**: $7/mo via Stripe → unlock key bypasses the limit

Free tier is intentionally tight here — SOQs use 8K output tokens × N prompts, so each call is significantly more expensive than a resume rewrite or cold email.

## Why this exists

Civil service panels score SOQs against a rubric pulled straight from the duty statement. Strong candidates still lose points when their responses don't mirror the posting's language. This tool does that reliably.

## Setup

```bash
cd soq-generator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
python app.py         # http://localhost:5002
```

The paywall is **off by default**. Drop Stripe keys into `.env` to turn it on.

## Stripe + deploy

Same shape as `resume-rewriter/` — see that directory's README for full Stripe setup, webhook configuration, and Render deploy walkthrough. Differences here:
- Webhook URL: `https://<your-app>/api/stripe/webhook`
- Free tier defaults to 1/day (override with `FREE_DAILY_LIMIT`)
- Default port 5002
- Gunicorn timeout bumped to 180s (SOQ generations can take longer than rewrites)

## What's next

- DOCX export (state panels sometimes require .docx upload)
- SOQ length enforcement (some postings cap at 2 pages or 1500 words)
- Multi-posting batch mode (one experience → N postings)
- Rubric-match scoring (estimate which MQs/DQs are weakly covered)
