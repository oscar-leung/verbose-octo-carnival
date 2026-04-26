# Cold Email Personalizer

Paste a recipient profile + your pitch. Get a personalized cold email + 3 subject lines you can drop straight into GMass or Apollo.

- **Claude Opus 4.7** with adaptive thinking + prompt caching on the system prompt
- **Structured outputs** (`output_config.format` with a JSON schema) — no flaky parsing
- **Free tier**: 5 emails per IP per 24h
- **Pro tier**: $7/mo via Stripe → unlock key bypasses the limit

## Setup

```bash
cd cold-email-personalizer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
python app.py         # http://localhost:5001
```

The paywall is **off by default**. Drop `STRIPE_SECRET_KEY` + `STRIPE_PRICE_ID` into `.env` to turn it on.

## Stripe + deploy

Same shape as `resume-rewriter/` — see that directory's README for full Stripe setup, webhook configuration, and Render deploy walkthrough. The only differences here:
- Webhook URL: `https://<your-app>/api/stripe/webhook`
- Free tier defaults to 5/day (override with `FREE_DAILY_LIMIT`)
- Default port 5001

## What's next

- CSV batch mode (recipient per row → personalized email per row, GMass-ready export)
- Reply-rate tracking via UTM-in-subject
- A/B variant generation
