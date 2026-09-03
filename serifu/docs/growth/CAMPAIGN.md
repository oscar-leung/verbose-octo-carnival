# Serifu — Campaign Ledger

Single source of truth for marketing operations. Maintained by campaign-manager;
copy comes from growth-marketer; anything only Oscar can do is queued in §3, never
marked done until he confirms. Rules that bind everything here: anime-agnostic in
public, honest and disclosed, no astroturf.

Last updated: 2026-09-03

---

## 1. Assets — shipped and ready

| Asset | Location | Where it gets used | Status |
|---|---|---|---|
| SEO guide: speaking practice with anime (pillar) | `public/guide/speaking-practice-with-anime.html` | Organic search cluster head; linked from launch posts once indexed | **Shipped** (live at `/guide/`) |
| SEO guide: shadowing Japanese | `public/guide/shadowing-japanese.html` | Organic search; internal links to pillar | **Shipped** |
| SEO guide: watch-party language learning | `public/guide/watch-party-language-learning.html` | Organic search; highest-intent CTA into the app | **Shipped** |
| SEO guide #4: Japanese subtitle files (.srt/.vtt/.ass) | `public/guide/japanese-subtitle-files.html` | Organic search (highest volume in plan); money-path CTA into the app; in hub + sitemap | **Shipped** |
| SEO guide #7: scared to speak Japanese | `public/guide/scared-to-speak-japanese.html` | Organic search ("japanese speaking anxiety"); shareable evergreen, soft CTA; in hub + sitemap | **Shipped** |
| Guide hub | `public/guide/index.html` | Hub-and-spoke internal linking | **Shipped** |
| og-image share card + meta tags | site `<head>` + og image in `public/` | Makes every Reddit/HN/X link unfurl properly — free CTR on all social pushes | **Shipped** |
| robots.txt + sitemap.xml | `public/robots.txt`, `public/sitemap.xml` | Search Console submission (§3.1). Note: sitemap host must be updated when the custom domain lands | **Shipped** |
| Store-listing pack (title, descriptions, keywords, shot list) | `docs/growth/store-listing.md` | Play Console listing (§3.6) | **Shipped**, unused until Play Console exists |
| Launch posts ×4 (r/LearnJapanese, r/languagelearning, Show HN, X thread) | `docs/growth/launch-posts.md` | Community launch sequence (§3.3), one at a time | **Shipped**, awaiting sequence gate |
| SEO content plan (10 articles; 5 written, 5 remaining) | `docs/growth/seo-content-plan.md` | Governs guide production; §6 briefs for #4 and #7 fulfilled 2026-09-03 | **Shipped** (plan) |
| ☕ support-link code (footer, Landing + SoloPractice) | `client/src/components/Landing.tsx:112`, `SoloPractice.tsx:259` | Renders only when `VITE_SUPPORT_URL` is set — dormant until Ko-fi exists (§3.2) | **Shipped, dormant** |

## 2. Sequencing gates (why nothing else moves yet)

1. **Donations link live before any traffic push.** The support link is code-complete
   but dormant; a launch post before Ko-fi + env var wastes the one first-impression
   spike we get per community.
2. **Guides indexed before social.** Search Console + sitemap submission first, so
   launch-post traffic lands on pages Google already knows about and backlinks count.
3. **One community at a time, one week to learn.** r/LearnJapanese first (its rules
   fit a disclosed builder post best), then read the feedback for a week before the
   next post.

## 3. Waiting on Oscar — queued checklists

### 3.1 Google Search Console + sitemap (unblocks indexing — do first)
- [ ] Sign in at https://search.google.com/search-console and add the live site as a URL-prefix property
- [ ] Verify ownership (HTML-file or meta-tag method; ask Claude to commit the token file if needed)
- [ ] Submit `sitemap.xml` (already live; source: `serifu/public/sitemap.xml`)
- [ ] Request indexing for `/guide/` and the three guide pages

### 3.2 Ko-fi + support link (unblocks all traffic pushes)
- [ ] Create a Ko-fi page (~10 min; Ko-fi over BMC per `docs/BUSINESS.md` §3 — 0% one-time fee)
- [ ] Anime-agnostic page copy; blurb exists in `docs/BUSINESS.md` §6 ("Serifu is free. If it's part of your week, you can buy the servers a coffee ☕")
- [ ] In Render → Environment, set `VITE_SUPPORT_URL=https://ko-fi.com/<handle>` and redeploy
- [ ] Confirm the ☕ link renders in the app footer on the live site

### 3.3 Launch posts (gated on 3.1 + 3.2 + 3.4; one at a time)
- [ ] Post #1 to r/LearnJapanese from your personal account — copy is ready to paste in `docs/growth/launch-posts.md` §1; check the subreddit's current self-promo rules on the day
- [ ] Reply to every comment for 48 h; log feedback + metrics in §5 here
- [ ] **Wait one week.** Then queue r/languagelearning (§2 of launch-posts.md), then Show HN (§3), then the X thread (§4) — same one-week spacing, adjusting copy per what the previous post taught us (route learnings to growth-marketer)

### 3.4 Render deployment verification (pre-flight for everything above)
- [ ] Confirm Render deploy of `main` is green and `https://<app>.onrender.com/healthz` returns `{"ok":true}` (runbook: `serifu/RELEASE.md` §1)
- [ ] Two-device smoke: create a room phone + laptop, load demo scene, play
- [ ] Confirm `/guide/`, `/robots.txt`, `/sitemap.xml`, and the og-image all load on the live URL

### 3.5 Custom domain (unlocks Play Store; improves all SEO)
- [ ] Buy domain (~$12/yr) and connect via Render → Settings → Custom Domains
- [ ] Tell Claude — sitemap.xml, robots.txt, and og/meta URLs must be updated to the new host, and Search Console needs the new property + re-submitted sitemap

### 3.6 Play Console (gated on 3.5 — TWA requires the custom domain)
- [ ] Create Google Play developer account ($25 one-time)
- [ ] Then hand off to Claude/store-ops: Bubblewrap TWA build (`RELEASE.md` §2) + listing copy from `docs/growth/store-listing.md` + screenshots per its shot list

## 4. Next 30 days — sequence

| Window | Action | Owner | Gate |
|---|---|---|---|
| Week 1 (Sep 3–9) | Render verification (3.4) → Search Console + sitemap (3.1) → Ko-fi + env var (3.2) | Oscar | none — this is the critical path |
| Week 1 | Briefs for SEO articles #4 and #7 delivered (§6) | campaign-manager | done below |
| Week 2 (Sep 10–16) | Growth-marketer writes article #4 (subtitle files guide); ship to `/guide/` + sitemap once approved | growth-marketer / Claude | briefs in §6 |
| Week 2 | Confirm guides show impressions in Search Console; then post #1 to r/LearnJapanese (3.3) | Oscar | 3.1 + 3.2 live |
| Week 3 (Sep 17–23) | Learning week: harvest r/LearnJapanese feedback into §5; growth-marketer writes article #7; no new posts | all | post #1 shipped |
| Week 4 (Sep 24–30) | Post #2 to r/languagelearning (copy revised per learnings); buy custom domain (3.5) in parallel | Oscar | week-3 review done |
| Early Oct | Show HN, then X thread, one week apart; Play Console (3.6) once domain is live | Oscar | prior posts reviewed |

Not scheduled: any paid promotion, cross-posting, or a second simultaneous community — against the one-at-a-time rule.

## 5. Results (fill in as known)

**Measurement reality check:** the app has no analytics, and the privacy policy
promises no tracking — so "visitors" and "room creations" are not directly
measurable today. What we *can* read honestly: Search Console impressions/clicks,
Ko-fi dashboard, Reddit/HN post metrics, and (later) Play Console installs.
Adding even privacy-friendly analytics (e.g. self-hosted Plausible, per
BUSINESS.md §6 week 4–5) would require a privacy-policy change — that is a
**biz-strategist + Oscar decision, not mine**. Recommendation: stay
Search-Console-only for now; it's free, privacy-respecting, and enough to steer
the SEO plan. Revisit when the Phase 2 trigger question (monthly actives) needs
a real number.

| Period | GSC impressions | GSC clicks | Site visitors | Rooms created | Ko-fi donations | Notes |
|---|---|---|---|---|---|---|
| Sep 2026 | — | — | n/a (no analytics) | n/a (no analytics) | — | baseline month |
| Oct 2026 | — | — | n/a | n/a | — | |

Per-post results (fill after each launch post):

| Post | Date | Upvotes/points | Comments | Top learning |
|---|---|---|---|---|
| r/LearnJapanese | — | — | — | — |
| r/languagelearning | — | — | — | — |
| Show HN | — | — | — | — |
| X thread | — | — | — | — |

## 6. Briefs for growth-marketer

**Brief — Article #4, "How to Get Japanese Subtitles for Any Show (.srt, .vtt, .ass Explained)" → `/guide/japanese-subtitle-files` (target: week 2).**
Write the practical sourcing-and-formats guide from the content plan: where learners
legitimately find Japanese subtitle files (subtitle archives like jimaku/kitsunekko-class
sites, extracting from owned media), an honest one-paragraph legality note, and a plain
explanation of the three formats — .srt (timing only), .vtt (web-native), .ass (styling
and the speaker tags that matter for character-claiming). This is the highest-search-volume
piece in the plan and a "money path" page: it should be genuinely useful with no tool at
all, mention Serifu exactly once as the app that imports all three formats into a furigana
script, end with the single clearly-marked CTA into the app, link up to the pillar guide
(`/guide/speaking-practice-with-anime.html`) in the intro, and stay strictly anime-agnostic
(formats and genres, never show names). Match the tone and HTML structure of the three
shipped guides in `public/guide/`.

**Brief — Article #7, "Too Scared to Speak Japanese? A Gentler Path Than Talking to Strangers" → `/guide/scared-to-speak-japanese` (target: week 3).**
Write the empathy-led anxiety piece: open by validating that speaking is the most-avoided
skill because tutors feel like interviews and strangers are terrifying, then build the
exposure-ladder argument — scripted lines are lower-stakes than free conversation, friends
are lower-stakes than strangers, and rehearsing a character's words removes the "what do I
even say" load entirely. Target the queries "afraid to speak japanese" / "japanese speaking
anxiety". Per the plan's money-path rule this is a shareable evergreen piece, not a hard-sell:
link to the shipped shadowing guide (`/guide/shadowing-japanese.html`) and up to the pillar,
mention Serifu once, no aggressive CTA. Keep it honest — no claims that the method cures
anxiety, just that graded, social, scripted speaking is an easier first rung. Anime-agnostic
throughout; tone should read like the r/LearnJapanese launch post's first paragraph, which
is our best-tested voice for this feeling.

## 7. Change log

- 2026-09-03 — Ledger created. Inventoried shipped assets, queued the six Oscar
  checklists, sequenced the next 30 days, delivered briefs for articles #4 and #7.
- 2026-09-03 — growth-marketer shipped articles #4 (`guide/japanese-subtitle-files.html`)
  and #7 (`guide/scared-to-speak-japanese.html`) per the §6 briefs; both added to the
  guide hub and `sitemap.xml`. §6 briefs fulfilled.
