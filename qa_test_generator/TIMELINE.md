# QA Test Case Generator — Roadmap

Living doc. Update as we ship. Target dates assume ~10 hrs/week of solo
focus and slip on real life.

> Today: **2026-04-24**

---

## Phase 0 — Foundation (✅ Shipped)

| Item | Status | Commit |
|---|---|---|
| Next.js 14 scaffold + Tailwind | ✅ | `d80a7de` |
| Anthropic SDK with `claude-opus-4-7` + adaptive thinking + JSON-schema structured output | ✅ | `d80a7de` |
| Anonymous-cookie session + Upstash daily quota (3/day free) | ✅ | `7c0773e` |
| Stripe Checkout + webhook → unlimited for subscribers | ✅ | `7c0773e` |
| Exports: CSV, JSON, **Jira**, **Xray**, **TestRail** | ✅ | `7c0773e` |
| Vercel deploy config (`vercel.json`) | ✅ | `7c0773e` |

**Decision points still open (user owns):**
- [ ] Sign up for Stripe + create `$9/mo` Price
- [ ] Sign up for Upstash + create Redis DB
- [ ] Run `npx vercel` and add env vars
- [ ] Wire Stripe webhook secret after first deploy
- [ ] Buy a domain (suggest something like `qatests.dev`, `testcaseai.io`, `specsmith.app`)

---

## Phase 1 — Vision input (🚧 In progress, this commit)

Read screenshots of an app/website → generate test cases for the observed UI.

| Item | Status |
|---|---|
| `/api/generate` accepts `screenshots[]` (base64 PNG/JPEG) | 🚧 |
| Client-side image resize (≤ 2000px long edge) before upload | 🚧 |
| Drag-drop, click-to-upload, paste-from-clipboard | 🚧 |
| Thumbnail previews with remove button | 🚧 |
| System prompt updated for visual reasoning | 🚧 |
| Feature description becomes optional when screenshots present | 🚧 |

**Why this matters:** Opus 4.7 ships 1:1 pixel-accurate vision up to 2576px on the long edge. This is the single biggest demo lever — *paste 3 Figma screens, get 25 test cases*. Sells better than "describe your feature."

**Target ship:** end of week (2026-04-30).

---

## Phase 2 — URL crawl (✅ Shipped v1; multi-page + auth pending)

Paste a public URL → server screenshots it → vision pipeline runs as Phase 1.

| Item | Status | Commit |
|---|---|---|
| URL input + desktop/mobile viewport toggle | ✅ | `8f90a1c` |
| `lib/screenshot.ts` — ScreenshotOne adapter | ✅ | `8f90a1c` |
| `/api/screenshot` route (URL validation, viewport, full-page capture) | ✅ | `8f90a1c` |
| Shared client-side resize pipeline (`dataUrlToScreenshot`) | ✅ | `8f90a1c` |
| Multi-page crawl (login → dashboard → settings) | ⏳ v2.1 | — |
| Auth'd screenshots (cookies / OTP / SSO) | ⏳ v3 | — |

**Decision points still open (user owns):**
- [ ] Sign up at screenshotone.com (100 free/month, $9/mo for 1k)
- [ ] Add `SCREENSHOTONE_ACCESS_KEY` to `.env.local` and Vercel env

**Risk:** Authenticated apps need a session cookie / login flow. v2.1 = multi-page (follow links at depth=2); v3 = "log in for me." Most paying customers will need v3 — start sales conversations to learn which auth modes matter first (Google SSO vs Okta vs basic email/password).

---

## Phase 3 — Mobile app crawl (⏳)

Upload `.apk` / `.ipa` → spin up Appium → traverse UI → generate test cases.

| Item | Notes |
|---|---|
| `.apk` upload + storage (S3 / Vercel Blob) | Trivial |
| Android crawl via Appium + emulator | BrowserStack App Automate or Sauce Labs API; ~$1/run |
| iOS crawl via XCUITest | Apple-licensed simulators — likely BrowserStack only |
| Generate XCUITest / Espresso scaffolding alongside cases | Stretch |

**Target:** 6–12 weeks (2026-06 → 2026-07). Build only after Phase 1+2 have ≥10 paying customers asking for it.

**Risk:** Real cost per crawl is non-trivial ($1–$5 per app). Need to gate this behind a higher tier ($49/mo Pro or $199/mo Team) or charge per crawl.

---

## Phase 4 — CI/CD push integrations (⏳)

Generated test cases auto-pushed into the customer's existing tools.

| Integration | Difficulty | Why |
|---|---|---|
| Jira API (create Test issues directly) | 1 day | Already have Jira CSV — direct API is incremental |
| Xray REST | 1 week | OAuth + Xray-specific endpoints |
| TestRail REST | 1 week | OAuth + TestRail-specific endpoints |
| GitHub Actions (PR comment with test cases) | 2 days | `actions/checkout` + a small wrapper script |
| Linear / Asana / ClickUp | 2 days each | Lower priority |

**Target:** 4 weeks total (2026-05-15 → 2026-06-12), prioritize Xray + TestRail first (highest willingness to pay).

---

## Phase 5 — Go-to-market (ongoing, start day-of-launch)

| Channel | Cadence | Goal |
|---|---|---|
| Twitter/X demo videos (15s screenshot → tests) | 2/week | First 100 followers in QA niche |
| LinkedIn posts in SDET groups | 1/week | First 10 demo requests |
| Reddit `r/QualityAssurance`, `r/softwaretesting` | weekly value-add | Community signal |
| Product Hunt launch | once, week 4 | First 1k visitors |
| Cold-email 50 SDET managers offering free trial | week 2 | First 5 paying customers |
| SEO landing pages (`alternatives to testRigor`, `Xray test case generator`) | 1/week | Compounding traffic |

**Pricing target:** $9/mo solo, $49/mo Pro (vision + URL crawl), $199/mo Team (mobile + integrations + 5 seats).

---

## Milestones (success criteria)

| # | When | What |
|---|---|---|
| M1 | Week 1 | App live on prod, payment works end-to-end |
| M2 | Week 4 | First 10 free signups |
| M3 | Week 6 | First $1 paid (the hardest dollar) |
| M4 | Week 12 | $1,000 MRR |
| M5 | Week 26 | $10,000 MRR — quit-the-job line |

---

## Open architectural questions

- **Database?** Currently Upstash KV only. Once we add per-account history / team seats / usage analytics, need Postgres (Vercel Postgres, Neon, Supabase). Hold off until we have one paying customer.
- **Auth?** Anonymous cookie is fine for v1. Add magic-link auth (Clerk / Auth.js) when we add team seats — week 8+.
- **Test case storage?** Right now nothing is stored — generate, download, gone. Saving to a "library" + re-running is a Pro feature; needs DB.
- **Vision token cost** at $5/MTok input: ~$0.07/request with 3 full-res screenshots. At $9/mo for unlimited, break-even at ~120 generations/month. Watch this metric.
