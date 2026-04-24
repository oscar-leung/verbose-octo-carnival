# Deploy Runbook

Goal: go from `main` to a production URL accepting real payments in **~45 minutes**.

You need:
- A credit card (for Vercel, Anthropic pay-as-you-go, Stripe fees, optional Upstash / ScreenshotOne upgrades).
- A GitHub account connected to your repo.
- (Optional) A domain. Fine to start on `your-project.vercel.app`.

You do NOT need to paste any secrets into this file or into chat — all secrets go directly into Vercel's environment variable UI.

---

## Phase A — Sign up for external services (~15 min)

Do these in any order. Each one ends with "copy this value to a password manager / scratchpad" — you'll paste them all into Vercel in Phase C.

### 1. Anthropic (required — core model calls)

1. Create account: [console.anthropic.com](https://console.anthropic.com/).
2. Add billing (pay-as-you-go).
3. API Keys → "Create Key" → scope it to workspace "QA Test Generator".
4. **Save** → `ANTHROPIC_API_KEY = sk-ant-...`

Cost estimate: each generation with Opus 4.7 + max effort + adaptive thinking ≈ $0.05–$0.15. Budget $5/mo for early testing.

### 2. Upstash Redis (required — quota + subscription cache)

1. Create account: [console.upstash.com](https://console.upstash.com/).
2. Create Database → Regional, any region closest to your Vercel region. Free tier is plenty to start.
3. Database page → REST API section.
4. **Save**:
   - `UPSTASH_REDIS_REST_URL = https://...upstash.io`
   - `UPSTASH_REDIS_REST_TOKEN = A...`

### 3. Stripe (required for paid plan)

1. Create account: [dashboard.stripe.com/register](https://dashboard.stripe.com/register).
2. Finish KYC (business details, bank account). Stripe runs in **test mode** by default until KYC is complete — that's fine for initial deploy.
3. Developers → API keys → Secret key (test mode for now).
   - **Save** `STRIPE_SECRET_KEY = sk_test_...`
4. Product Catalog → "Add product":
   - Name: `QA Test Generator Pro`
   - Description: `Unlimited test case generations.`
   - Pricing: Recurring, $9.00 USD, monthly.
   - Save → click the Price row → copy the `price_...` ID.
   - **Save** `STRIPE_PRICE_ID = price_...`
5. Skip webhook setup for now — you'll come back in Phase D after you have a production URL.

### 4. ScreenshotOne (required for "Capture from URL" feature)

1. Sign up: [screenshotone.com](https://screenshotone.com/).
2. Dashboard → API keys.
3. **Save** `SCREENSHOTONE_ACCESS_KEY = ...`

Free tier is 100 screenshots/month. $9/mo for 1,000. Upgrade when you start getting real traffic.

### 5. (Optional) Custom domain

If you want `qatests.dev` or similar instead of `your-project.vercel.app`:
- Buy at Cloudflare Registrar (cheapest, ~$10/yr) or Namecheap.
- Hold on DNS config until Phase E — Vercel will tell you the exact CNAME.

---

## Phase B — Push branch to main (~2 min)

The feature branch is `claude/plan-utility-apps-4CjO9`. Before Vercel can import the project, it needs to be on `main`.

**Option 1: merge via GitHub PR**
```bash
# From your machine:
git checkout claude/plan-utility-apps-4CjO9
git pull
# Open https://github.com/oscar-leung/verbose-octo-carnival/pull/new/claude/plan-utility-apps-4CjO9
# Review, merge to main.
```

**Option 2: fast-forward merge**
```bash
git checkout main
git pull
git merge --ff-only claude/plan-utility-apps-4CjO9
git push origin main
```

Either works. GitHub PR is preferred if you want to see the diff first.

---

## Phase C — Vercel project import (~10 min)

1. Sign up for Vercel Pro ($20/mo): [vercel.com/pricing](https://vercel.com/pricing).
   - **Why Pro is required (not optional):** Hobby has a 10-second function timeout and a 4.5 MB request-body limit. Claude Opus 4.7 generations can take 20–90s; 6 base64 screenshots is ~8 MB. Both limits block the app on Hobby.
2. Dashboard → "Add New" → "Project" → Import your Git repository.
3. Configure:
   - **Root Directory:** `qa_test_generator` (critical — the app lives in a subfolder).
   - **Framework Preset:** Next.js (auto-detected).
   - **Build Command:** `next build` (default).
   - **Output Directory:** `.next` (default).
   - **Install Command:** `npm install` (default).
4. Before clicking Deploy, expand "Environment Variables" and paste each of the following (you already have most of these from Phase A):

| Name | Value source | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic console | Required |
| `UPSTASH_REDIS_REST_URL` | Upstash DB page | Required |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash DB page | Required |
| `STRIPE_SECRET_KEY` | Stripe dashboard | Start with test key |
| `STRIPE_PRICE_ID` | Stripe product you created | `price_...` |
| `STRIPE_WEBHOOK_SECRET` | **LEAVE BLANK** — fill in Phase D | — |
| `SCREENSHOTONE_ACCESS_KEY` | ScreenshotOne dashboard | Required for URL capture |
| `NEXT_PUBLIC_APP_URL` | `https://your-project.vercel.app` | You'll update this if you add a custom domain |
| `FREE_TIER_DAILY_LIMIT` | `3` | Override later if needed |

5. Click **Deploy**. First build takes ~90s.
6. Once deployed, your URL is `https://your-project.vercel.app`. Open it — the UI should render, sample chips should work, quota badge should show `3/3 free generations left today`.

---

## Phase D — Wire the Stripe webhook (~5 min)

1. Stripe dashboard → Developers → Webhooks → "Add endpoint".
2. **Endpoint URL:** `https://your-project.vercel.app/api/webhook`
3. **Events to send:** select these three:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Add endpoint → click into it → "Signing secret" → Reveal → copy.
5. Back in Vercel → Settings → Environment Variables → edit `STRIPE_WEBHOOK_SECRET` → paste the `whsec_...` value → Save.
6. Vercel → Deployments → redeploy the latest (or it will auto-redeploy on the env var change).

---

## Phase E — Smoke test (~5 min)

In an incognito window:

1. Open `https://your-project.vercel.app`.
2. Click a sample chip (e.g. "Password reset") → Generate → confirm test cases render.
3. Click "Upgrade to Pro" → Stripe Checkout opens.
4. Pay with Stripe's test card: `4242 4242 4242 4242`, any future expiry, any CVC, any ZIP.
5. On `/success`, wait 2–3 seconds, reload `/`. Quota badge should now say **Unlimited · Pro**.
6. Generate again without hitting the 3-per-day limit.

If any step fails, check:
- Vercel → Deployments → the current build → Functions → route → Logs.
- Stripe → Developers → Events → the most recent `checkout.session.completed` — does it show your endpoint returning 200?

---

## Phase F — Flip to live mode (only when you're ready for real money)

1. Stripe dashboard → toggle "Test mode" off (top right).
2. Rerun Phase A step 3 part 3 + step 4 in live mode — create a **new** $9/mo Price, grab the **live** secret key.
3. Update env vars in Vercel:
   - `STRIPE_SECRET_KEY` → live secret key
   - `STRIPE_PRICE_ID` → live price ID
4. Rerun Phase D: create a **live-mode** webhook endpoint, grab the live signing secret, update `STRIPE_WEBHOOK_SECRET` in Vercel.
5. Redeploy.
6. Test with a real card (your own) first — run a full subscription flow, confirm the money lands in your Stripe balance, then cancel the subscription from the Stripe dashboard.

---

## Phase G — (Optional) Custom domain

1. Vercel → Project → Settings → Domains → Add.
2. Enter your domain → follow the CNAME or A-record instructions for your registrar.
3. Wait for SSL provisioning (~2 min).
4. Update `NEXT_PUBLIC_APP_URL` in env vars to `https://yourdomain.com` (no trailing slash).
5. Update your Stripe webhook URL to `https://yourdomain.com/api/webhook` (and grab the new signing secret if Stripe regenerates it — usually it doesn't for URL changes).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `/api/generate` returns 500 "missing ANTHROPIC_API_KEY" | Env var not set or deploy was triggered before you added it | Add env var, redeploy |
| Generation times out after 60s | You're on Vercel Hobby, not Pro | Upgrade to Pro |
| `/api/screenshot` returns 501 | No `SCREENSHOTONE_ACCESS_KEY` | Sign up at screenshotone.com, add env var, redeploy |
| `/api/webhook` returns 400 "Invalid signature" | `STRIPE_WEBHOOK_SECRET` missing or wrong (test vs live) | Verify the secret matches the webhook endpoint's mode |
| Post-checkout, app still shows "free tier" | Webhook didn't fire or Redis keys not persisting | Stripe → Events → find the `checkout.session.completed` → did it return 200? If it returned 500, inspect Vercel function logs |
| URL capture times out | Target site blocks headless browsers or takes > 45s to load | Try a different URL; ScreenshotOne has per-plan timeouts |

---

## After deploy: monitoring

- **Vercel Analytics** (built-in, free tier) — track page views.
- **Stripe Billing alerts** — Settings → email alerts on new subscriptions / cancellations.
- **Anthropic usage** — console.anthropic.com → Usage. Set a spend alert at $50 until you know your unit economics.
- **Upstash dashboard** — watch daily ops count; free tier is 10k/day, plenty early on.
