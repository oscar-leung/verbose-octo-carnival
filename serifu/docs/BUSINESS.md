# Serifu — Business Plan

Owner: Oscar Leung · Status: pre-revenue · Goal: passive income from the platform, not the anime.
Legal frame (see RELEASE.md "Going commercial"): the Frieren IP is never monetized; the sellable
asset is the anime-agnostic platform, with Frieren as Oscar's private first use case.

**Strategy (Oscar's call, 2026-08-25): no subscription paywall today.** Phase 1 is
donation-supported — everything free, "Buy Me a Coffee"-style support links. A supporter
membership (Phase 2) only gets built if usage and server costs justify it. People genuinely like
supporting free tools, and a hard paywall is wrong for the product at its current size.

## 1. Positioning

Serifu is a **watch-party language-practice platform**: friends open the same episode of any show
(bring-your-own-media — video never leaves each device), the app keeps playback in sync, a furigana
script scrolls alongside, each person claims a character, and rehearsal mode pauses the video at your
line until you speak it well enough (live speech scoring, 0–100). Vocab flows into spaced repetition;
public per-scene URLs enable solo practice. Nobody else sells this: subtitle-learning tools are all
single-player. Serifu is the "Discord watch party × shadowing coach × Anki" that turns immersion
learning into a weekly social ritual — and social rituals retain, and retained users support the
tools they love. Frieren stays as the private demo Oscar runs with friends; the public brand ships
anime-agnostic with original demo dialogue only.

## 2. Competitor pricing

| Product | Price | Model | What Serifu has that they don't |
|---|---|---|---|
| Language Reactor | Free; Pro ~$8/mo | Freemium browser extension (Netflix/YouTube dual subs) | No sync, no rooms, no speaking practice — pure solo reading/listening |
| Migaku | ~$10/mo (~$84/yr) | Subscription browser extension + apps, cards from video | Solo tool; no watch party, no speech scoring against lines |
| LingQ | ~$13/mo (annual ~$8/mo) | Subscription content library + SRS | Its own content, not your shows; no video sync, no friends |
| Anki + ecosystem | Free (iOS app $25 once) | FOSS SRS; paid decks/add-ons around it | Zero video, zero social; Serifu can *export to* Anki, not compete with it |

The gap: every incumbent monetizes a **solo pipeline** (video → cards). None has the
**social/watch-party layer** — synced playback, character claiming, group rehearsal, voice chat.
That layer is naturally server-side, which is exactly what a future supporter tier can fund. If
Phase 2 ever ships, price under Migaku ($10) and near Language Reactor Pro ($8): **~$5/mo** remains
the right anchor. Today, though, we're the only fully-free option in this table — that's a
positioning asset, not a missed sale.

## 3. Phase 1 — Donations (now)

**Everything is free.** No accounts, no Stripe, no feature gates. The ask is a support link
("Buy me a coffee ☕ / 開発を応援する") in the app footer and README.

### Platform choice: Ko-fi over Buy Me a Coffee

| | Buy Me a Coffee | Ko-fi |
|---|---|---|
| One-time donation fee | 5% (+ payment processing) | **0%** (payment processing only, ~2.9% + $0.30 via Stripe/PayPal) |
| Recurring memberships | 5% | 5% (0% with Ko-fi Gold, $8/mo — not worth it at our scale) |
| Setup | ~10 minutes | ~10 minutes |

**Call: Ko-fi.** 0% on one-time donations — which will be most of the money — and identical setup
effort. Either works; the fee difference is the tiebreaker.

### Honest donation math

Typical free-tool/OSS donation conversion is **~0.1–0.5% of monthly *active* users**, average
one-time donation **$3–8**, plus a handful of recurring members at **$3–5/mo** once there's a real
community. (Note: active users, not visitors — a stricter base than the old funnel used.)

| Monthly actives | One-time donors/mo (0.1–0.5%) | One-time $/mo | Recurring members | Recurring $/mo | **Total/mo** |
|---|---|---|---|---|---|
| 100 | 0–1 (round down: most months, zero) | $0–8 | 0 | $0 | **~$0–8** |
| 1,000 | 1–5 | $3–40 | 1–3 @ $3–5 | $3–15 | **~$5–50** |
| 10,000 | 10–50 | $30–400 | 10–25 @ $3–5 | $30–125 | **~$60–500** |

This is coffee money at small scale — **and that's fine.** What Phase 1 buys:
- **Zero infrastructure:** no accounts, no database, no Stripe webhooks, no feature gates to build
  or maintain. The current in-memory server stays exactly as it is.
- **Zero support burden:** no billing disputes, no "restore my subscription", no churn dashboards.
- **Works TODAY:** first dollar is gated on a 10-minute Ko-fi signup, not 8 weeks of auth + payments.
- **Goodwill compounds:** a genuinely free tool is easier to recommend in r/LearnJapanese and
  Discord servers than a freemium one — and word-of-mouth is the entire growth plan (§5).

Break-even check: baseline burn is ~$8/mo (Render Starter + domain, §6). At 1,000 monthly actives,
donations plausibly cover the server bill. Below that, Serifu costs Oscar about two coffees a month
to run — an acceptable price for a growing funnel.

## 4. Phase 2 — Supporter tier (later, only if earned)

**Trigger, not date.** Build this only when at least one of these is true:
- The server bill materially exceeds donations (e.g. TURN bandwidth or a required Postgres tier
  pushes burn past ~$25–30/mo with donations not keeping up), or
- Users are *asking* for hosted conveniences (accounts/sync, hosted galleries, big rooms) in numbers
  that suggest real willingness to pay.

**Framing: supporter membership, not paywall.** Everything currently usable stays free forever —
solo practice via scene URLs, rooms up to 4, bring-your-own-media + subtitle import, speech scoring,
local SRS/wordbook, script editor, STUN-only voice. Supporters (~$5/mo, ~$40/yr) fund the servers
and get the hosted conveniences as thanks:

| Supporter perk | Why it's worth supporting for | Why it's legitimately server-funded |
|---|---|---|
| Hosted script gallery | Save prepped episodes server-side; share by link; your group loads ep. 12 in one click instead of re-importing JSON | Real storage + moderation cost; "export JSON, paste to friends" remains the free path |
| Cross-device sync (accounts) | Mastery scores + wordbook follow you phone↔laptop; today a cleared cache erases everything | Requires accounts + a database — infrastructure the free client-side model doesn't need |
| Rooms >4 people | Clubs, classes, Discord servers | WebRTC mesh cost grows quadratically; bigger rooms mean real relay/SFU spend |
| TURN relay voice | Voice that works on campus/corporate/symmetric-NAT networks, guaranteed | TURN is metered bandwidth Oscar pays per GB — the clearest cost-passthrough in the product |
| Priority episode-prep tooling | Auto-furigana (kuromoji), speaker auto-tagging, timing auto-shift — 15 min/episode drops toward 2 | Server-side compute; also the feature power users ask for first |

Rule of thumb (unchanged, now the supporter-tier rationale): **free = your device does the work;
supporters = our server does the work.** The free tier stays genuinely good (the word-of-mouth
engine), and every supporter perk has a defensible cost story rather than an artificial gate.

If/when Phase 2 triggers, the old subscription math still applies as the ceiling: ~1–2% of visitors
converting at $5/mo → roughly $50–100 MRR at 1k visitors/mo, $500–1,000 at 10k, with ~5% monthly
churn and 12–24 months of compounding to get there. That model is parked, not deleted.

## 5. Passive-income reality check

Honest notes (donations edition):
- Donations scale with **love, not traffic** — the conversion driver is moments of delight (a group
  finishing its first episode, a passed rehearsal streak). A well-timed, non-nagging "enjoying
  Serifu? ☕" beats a footer link nobody sees. One prompt surface, never a modal.
- "Passive" still means the **content compounds** — SEO posts ("how to shadow anime with friends",
  "jimaku.cc workflow", "Web Speech API Japanese scoring"), a public scene-URL gallery that indexes,
  Reddit/Discord word-of-mouth in r/LearnJapanese and anime-club servers. Writing that content is
  work; it just doesn't scale with users.
- Zero-work income does not exist at this stage: expect ~2–4 hrs/week on content + support after
  launch. What Phase 1 removes is the *build* work (no auth/payments) and the *ops* work (no billing
  support), not the growth work.
- The watch-party angle is the growth hack: every room invite is a referral. Optimize the
  invite → first-scene experience above all else. A free product makes the invite easier to send.

## 6. 90-day roadmap to first dollar

Week 1 — **First dollar, immediately**
- [Oscar] Create Ko-fi page (10 minutes). Optional: BMC too, but Ko-fi's 0% one-time fee wins (§3).
- [Claude] Ship the support link in the app footer + README ("Serifu is free. If it's part of your
  week, you can buy the servers a coffee ☕"). Anime-agnostic copy, Japanese-first label.
- [Oscar] Buy domain (~$12/yr), point it at Render; upgrade Render to Starter $7/mo (no cold starts
  once traffic matters — can defer to launch week to save a few dollars).
- **This is the first-dollar gate — day 7, not week 8.**

Weeks 2–3 — **Rebrand + polish**
- [Claude] Rebrand pass: anime-agnostic landing page, replace demo scene with original dialogue,
  "works with any show" copy. Keep Frieren assets out of the public build.
- [Claude] Onboarding funnel: invite link → demo scene in <60 s.

Weeks 4–5 — **Launch**
- [Oscar] Post to r/LearnJapanese, Hacker News (Show HN), 2–3 Japanese-learning Discords; ask 5
  friends' groups to run a session. "Completely free, donation-supported" is the headline — lead
  with it.
- [Claude] Landing page polish, basic analytics (self-hosted Plausible or simple event counts) —
  we need the monthly-actives number to know when Phase 2 triggers.

Weeks 6–9 — **Compound**
- [Oscar] Two SEO posts (episode-prep workflow; shadowing-with-friends guide).
- [Claude] Auto-furigana prep tooling v1 (kuromoji) — ships free; it's the feature power users ask
  for first and the strongest word-of-mouth generator. Fix whatever launch feedback surfaced.
- [Claude] One tasteful in-app "buy us a coffee" moment (e.g. after a group finishes an episode).

Weeks 10–13 — **Measure, decide**
- [Oscar] Review the numbers: monthly actives, donation total, server bill. If the Phase 2 trigger
  (§4) isn't met — and at <1k actives it won't be — stay in Phase 1 and keep compounding.
- [Oscar] Optional: Play Store account ($25) + [Claude] Bubblewrap TWA build.

**Phase 2 backlog** (parked until the §4 trigger fires — do not build early):
- [Claude] Auth (email magic-link), user table, local-first mastery/wordbook sync.
- [Oscar] Stripe account; 1-page privacy policy + ToS (template).
- [Claude] Hosted script gallery (CRUD + share links, private-by-default), room-size gating (>4),
  TURN credential gating (metered.ca creds already supported via `/api/ice`).
- [Oscar] metered.ca TURN account (free 20 GB tier to start).
- [Claude] Stripe Checkout + customer portal + webhook → supporter flag; annual plan at checkout.

First dollar target: **week 1** (a single Ko-fi donation from an early user or friend group counts —
honestly). Realistic Phase 1 steady state: **$5–50/mo at ~1k monthly actives**, reached over months
of compounding, not 90 days.

## 7. Cost sheet

| Item | Cost | When |
|---|---|---|
| Render Starter | $7/mo | Week 1 (or defer to launch) |
| Domain | ~$12/yr (~$1/mo) | Week 1 |
| Ko-fi | $0 platform fee on one-time; processor ~2.9% + $0.30/txn | Per donation |
| TURN (metered.ca) | $0 (20 GB free) → ~$0.40/GB after | Phase 2 only |
| Postgres | $0 → $7/mo | Phase 2 only |
| Stripe | 2.9% + $0.30/txn | Phase 2 only |
| Google Play | $25 one-time | Optional, week 10+ |
| Apple Developer | $99/yr | Defer — PWA covers iOS |

Baseline burn: **~$8/mo** (Render + domain). Phase 1 break-even: **~2 coffees a month** — plausible
from ~1,000 monthly actives (§3), and until then the downside is bounded at $8/mo. No Phase 2 cost
appears before Phase 2 revenue justifies it: the cost sheet is trigger-gated by construction.

## The core bet

A genuinely free social layer on top of everyone else's paid solo tools, supported by the people who
love it: donations cover the ~$8/mo bill at modest scale, and a supporter membership (funding the
server-side conveniences, never gating the core) exists as a pre-designed Phase 2 the moment usage
earns it. Cheap to run, legal by construction (bring-your-own-media, original demo content), grown
by the product's own invite links plus slow SEO — and easier to spread precisely because there's no
paywall in the invite.
