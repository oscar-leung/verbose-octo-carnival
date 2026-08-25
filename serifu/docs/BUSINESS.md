# Serifu — Business Plan

Owner: Oscar Leung · Status: pre-revenue · Goal: passive income from the platform, not the anime.
Legal frame (see RELEASE.md "Going commercial"): the Frieren IP is never monetized; the sellable
asset is the anime-agnostic platform, with Frieren as Oscar's private first use case.

## 1. Positioning

Serifu is a **watch-party language-practice platform**: friends open the same episode of any show
(bring-your-own-media — video never leaves each device), the app keeps playback in sync, a furigana
script scrolls alongside, each person claims a character, and rehearsal mode pauses the video at your
line until you speak it well enough (live speech scoring, 0–100). Vocab flows into spaced repetition;
public per-scene URLs enable solo practice. Nobody else sells this: subtitle-learning tools are all
single-player. Serifu is the "Discord watch party × shadowing coach × Anki" that turns immersion
learning into a weekly social ritual — and social rituals retain, and retained users pay. Frieren
stays as the private demo Oscar runs with friends; the public brand ships anime-agnostic with
original demo dialogue only.

## 2. Competitor pricing

| Product | Price | Model | What Serifu has that they don't |
|---|---|---|---|
| Language Reactor | Free; Pro ~$8/mo | Freemium browser extension (Netflix/YouTube dual subs) | No sync, no rooms, no speaking practice — pure solo reading/listening |
| Migaku | ~$10/mo (~$84/yr) | Subscription browser extension + apps, cards from video | Solo tool; no watch party, no speech scoring against lines |
| LingQ | ~$13/mo (annual ~$8/mo) | Subscription content library + SRS | Its own content, not your shows; no video sync, no friends |
| Anki + ecosystem | Free (iOS app $25 once) | FOSS SRS; paid decks/add-ons around it | Zero video, zero social; Serifu can *export to* Anki, not compete with it |

The gap: every incumbent monetizes a **solo pipeline** (video → cards). None has the
**social/watch-party layer** — synced playback, character claiming, group rehearsal, voice chat.
That layer is also naturally server-side, which is exactly what you can charge for. Price under
Migaku ($10) and near Language Reactor Pro ($8): **$5/mo**.

## 3. Free vs Paid

Keep free what is already free — it's the funnel and it costs the server almost nothing:

**Free forever:** solo practice via scene URLs, 1 active room (up to 4 people), bring-your-own-media
and subtitle import, speech scoring, local SRS/wordbook, script editor, STUN-only voice.

**Serifu Plus — $5/mo (or $40/yr):** service-layer value only.

| Paid feature | Why it's worth paying for | Why it's legitimately paid |
|---|---|---|
| Hosted script gallery | Save prepped episodes server-side; share by link; your group loads ep. 12 in one click instead of re-importing JSON | Real storage + moderation cost; the current "export JSON, paste to friends" flow is the free fallback |
| Cross-device sync (accounts) | Mastery scores + wordbook follow you phone↔laptop; today a cleared cache erases everything | Requires accounts + a database — infrastructure that doesn't exist in the free client-side model |
| Rooms >4 people | Clubs, classes, Discord servers | WebRTC mesh cost grows quadratically; bigger rooms mean real relay/SFU spend |
| TURN relay voice | Voice that works on campus/corporate/symmetric-NAT networks, guaranteed | TURN is metered bandwidth Oscar pays per GB — the clearest cost-passthrough in the product |
| Priority episode-prep tooling | Auto-furigana (kuromoji), speaker auto-tagging, timing auto-shift — 15 min/episode drops toward 2 | Server-side compute; also the feature power users ask for first |

Rule of thumb: **free = your device does the work; paid = our server does the work.** That keeps the
free tier genuinely good (word-of-mouth engine) while every paid feature has a defensible cost story.

## 4. Passive-income reality check

Funnel: visitors → free signups (~10% of visitors try a room/scene) → paid (1–2% of *visitors* is
generous for niche freemium; stated as % of visitors for honesty). At $5/mo:

| Monthly visitors | Paid @1% | MRR @1% | Paid @2% | MRR @2% |
|---|---|---|---|---|
| 100 | 1 | $5 | 2 | $10 |
| 1,000 | 10 | $50 | 20 | $100 |
| 10,000 | 100 | $500 | 200 | $1,000 |

With ~5% monthly churn, steady-state subscribers ≈ (new paid/mo) ÷ 0.05 — so 10k visitors/mo
sustaining ~$500–1,000 MRR is the realistic "nice side income" scenario, and it takes **12–24 months**
of compounding to get there, not 90 days.

Honest notes:
- "Passive" means the **content compounds** — SEO posts ("how to shadow anime with friends",
  "jimaku.cc workflow", "Web Speech API Japanese scoring"), a public scene-URL gallery that indexes,
  Reddit/Discord word-of-mouth in r/LearnJapanese and anime-club servers. Writing that content is
  work; it just doesn't scale with users.
- Zero-work income does not exist at this stage: expect ~2–4 hrs/week on content + support after
  launch, front-loaded build effort before it.
- The watch-party angle is the growth hack: every room invite is a referral. Optimize the
  invite → first-scene experience above all else.

## 5. 90-day roadmap to first dollar

Weeks 1–2 — **Foundation**
- [Oscar] Buy domain (~$12/yr), point it at Render, upgrade Render to Starter $7/mo (no cold starts once traffic matters — can defer to week 9 to save $14).
- [Claude] Rebrand pass: anime-agnostic landing page, replace demo scene with original dialogue, "works with any show" copy. Keep Frieren assets out of the public build.

Weeks 3–4 — **Accounts**
- [Claude] Auth (email magic-link — no password reset support burden), user table, migrate mastery/wordbook to sync when signed in (local-first, server-merged).
- [Oscar] Create Stripe account; write 1-page privacy policy + ToS (template).

Weeks 5–6 — **The paid features**
- [Claude] Hosted script gallery (CRUD + share links, private-by-default), room-size gating (>4 = Plus), TURN credential gating behind Plus (metered.ca creds already supported via `/api/ice`).
- [Oscar] Set up metered.ca TURN account (free 20 GB tier to start).

Weeks 7–8 — **Money**
- [Claude] Stripe Checkout + customer portal + webhook → `plus` flag on account; feature gates read it. Annual plan ($40) at checkout.
- [Oscar] Flip Stripe to live mode, run a real $5 test purchase. **This is the first-dollar gate.**

Weeks 9–10 — **Launch**
- [Oscar] Post to r/LearnJapanese, Hacker News (Show HN), 2–3 Japanese-learning Discords; ask 5 friends' groups to run a session.
- [Claude] Landing page polish, onboarding funnel (invite link → demo scene in <60 s), basic analytics (self-hosted Plausible or simple event counts).

Weeks 11–13 — **Compound**
- [Oscar] Two SEO posts (episode-prep workflow; shadowing-with-friends guide). Optional: Play Store account ($25) + [Claude] Bubblewrap TWA build.
- [Claude] Priority prep tooling v1 (auto-furigana via kuromoji) as the Plus headline feature; fix whatever launch feedback surfaced.

First dollar target: **week 8**. First $100 MRR: realistically month 4–6.

## 6. Cost sheet

| Item | Cost | When |
|---|---|---|
| Render Starter | $7/mo | Week 1 (or defer to launch, week 9) |
| Domain | ~$12/yr (~$1/mo) | Week 1 |
| TURN (metered.ca) | $0 (20 GB free) → ~$0.40/GB after | When Plus voice usage grows |
| Postgres (Render/Neon free tier) | $0 → $7/mo eventually | Week 3 |
| Stripe | 2.9% + $0.30/txn (~$0.45 of each $5) | Per sale |
| Google Play | $25 one-time | Optional, week 11+ |
| Apple Developer | $99/yr | Defer — PWA covers iOS; only if App Store demand appears |

Baseline burn: **~$8/mo** (Render + domain). Net per subscriber ≈ $4.55/mo.
**Break-even: 2 subscribers.** With Postgres paid tier and modest TURN usage (~$18/mo total):
**4 subscribers.** Everything past ~5 subscribers is profit — the risk here is time, not money.

## The core bet

A $5/mo social layer on top of a free solo tool, sold to the group organizer: one person in each
friend group pays so everyone's watch party works better. Cheap to run (break-even at 2 subs),
legal by construction (bring-your-own-media, original demo content), and grown by the product's own
invite links plus slow SEO — passive-ish by month 12, never by month 3.
