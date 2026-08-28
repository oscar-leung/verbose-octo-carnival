# Resume Bullet Rewriter

Paste a job description + your experience. Get 5-8 tailored resume bullets optimized for that role.

- **Claude Opus 4.7** with adaptive thinking + prompt caching on the system prompt
- **Structured outputs** (`output_config.format` with a JSON schema) — guaranteed parseable responses
- **Free tier**: 3 rewrites per IP per 24h
- **Pro tier**: $7/mo via Stripe subscription → unlock key bypasses the rate limit

## Architecture

```
app.py          Flask server, routes, auth middleware
store.py        SQLite unlock-key store (created/read/deactivated by billing events)
ratelimit.py    Per-IP sliding-window limiter for the free tier
billing.py      Stripe checkout session + webhook handler
templates/      index.html (main form) + unlocked.html (post-checkout landing)
```

The paywall is **off by default**. If `STRIPE_SECRET_KEY` and `STRIPE_PRICE_ID` are unset, the app runs in free mode with no limits. Drop keys in `.env` to enable billing.

## Local setup

```bash
cd resume-rewriter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
python app.py          # http://localhost:5000
```

## Stripe setup

1. In Stripe Dashboard, create a **recurring Price** for $7/mo. Copy the price ID (`price_...`).
2. Add `STRIPE_SECRET_KEY` and `STRIPE_PRICE_ID` to `.env`.
3. For webhook testing: `stripe listen --forward-to localhost:5000/api/stripe/webhook` → copy the printed `whsec_...` into `STRIPE_WEBHOOK_SECRET`.
4. Trigger a test event: `stripe trigger checkout.session.completed`.

Events handled:
- `checkout.session.completed` — mints a new unlock key, stores it in SQLite
- `customer.subscription.deleted` — marks the unlock key inactive

## User flow

1. User submits a rewrite; server records the hit in the IP's sliding window.
2. After 3 hits, `/api/rewrite` returns 429 with `code: "rate_limited"` and the UI shows the upgrade CTA.
3. User clicks subscribe → `/api/checkout` → Stripe Checkout → redirects to `/unlocked?session_id=...`.
4. `/unlocked` verifies the session with Stripe, mints an unlock key (idempotent vs. the webhook), shows it.
5. "Start rewriting →" redirects home with `?unlock_key=...` in the URL; the page stores it in `localStorage` and attaches it as `X-Unlock-Key` on every subsequent request.

## Deploy

Procfile + `runtime.txt` are included for Render / Heroku / Fly (buildpack-style).

**Render.com (one-click-ish):**
1. New → Web Service → connect this repo → root dir `resume-rewriter`
2. Build: `pip install -r requirements.txt`
3. Start: `gunicorn -c gunicorn.conf.py app:app`
4. Env vars: `ANTHROPIC_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET`, `WEB_CONCURRENCY=2`
5. Disk: attach a small persistent disk mounted at e.g. `/var/data`, then set `UNLOCK_DB_PATH=/var/data/unlock.db` so the DB survives redeploys.
6. Stripe webhook URL: `https://<your-app>.onrender.com/api/stripe/webhook`

**PythonAnywhere:** same `.env`, use the Flask app wizard and point to `app.py:app`.

## Known limitations

- Rate limiter is in-memory per-process. Multi-worker deploys (`WEB_CONCURRENCY>1`) mean the effective free limit is `FREE_DAILY_LIMIT × workers`. For real scale, swap `ratelimit.py` for Redis INCR+EXPIRE.
- No email on subscribe — unlock key is shown once on the success page. Add SES/Resend if you want recovery flow beyond "reply to your Stripe receipt."
- No admin panel. `unlock.db` is a regular SQLite file; `sqlite3 unlock.db` is your admin.
