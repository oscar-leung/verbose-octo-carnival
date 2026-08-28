# Launch Copy

Ready-to-edit templates for the first 30 days. Replace `YOUR_URL` with your
deployed domain (e.g. `https://qatests.dev` or `https://your-project.vercel.app`)
before posting.

---

## Day 0 — Quiet launch (1 post, 1 Reddit comment)

Ship the app live, then do one low-stakes post to validate messaging before
putting your name on the line with a big launch.

### Twitter/X — "Soft launch" thread (4 tweets)

> 1/ Wrote a tool for my own QA workflow: paste a feature spec, get 15+
> structured test cases covering happy path, edges, security, a11y.
>
> YOUR_URL
>
> 2/ It exports straight to Jira CSV, Xray CSV, TestRail CSV, or generic
> CSV/JSON. Cuts the "write 50 test cases by hand" part of the job down
> to 30 seconds.
>
> 3/ It also reads screenshots. Drop in a Figma export or screenshot of
> your app, and it grounds the test cases in what's actually on screen.
> Paste a URL and it'll crawl up to 5 same-origin pages.
>
> 4/ Free tier: 3 generations/day. Pro: $9/mo unlimited. Still rough
> around the edges but it's saving me hours every week. Happy to swap
> notes with any SDETs.

### Reddit — r/QualityAssurance or r/softwaretesting

Post in the weekly "what are you working on" or "show and tell" thread, NOT
as a standalone post (standalone self-promo gets removed):

> Been writing test cases by hand forever. Built a small tool that reads
> a feature spec (or screenshots of the UI) and generates ~15 structured
> test cases with exact steps and expected results — exports to Jira /
> Xray / TestRail.
>
> Free tier is 3/day, no sign-up. Would love feedback on what's missing
> for your workflow: YOUR_URL

---

## Week 1 — LinkedIn post (long-form, for the SDET network)

Post Tuesday or Wednesday morning, 9–10am in your timezone.

> After writing my ten-thousandth test case by hand, I built a small
> tool to stop doing that.
>
> Paste a feature spec. Get 15–25 structured test cases covering:
> → happy paths
> → edge cases (empty, max, unicode, boundary)
> → negatives (invalid input, expired session, over-privileged role)
> → security (SQL injection, XSS on free-text fields)
> → accessibility (keyboard nav, WCAG AA contrast, touch targets)
>
> Export to Jira, Xray, TestRail, or plain CSV. Or push directly to
> Jira via API.
>
> Vision input: drop in screenshots of your app, it grounds every test
> in visible UI — no hallucinated buttons.
>
> URL input: paste a public page and it'll crawl up to 5 linked pages
> to build a multi-screen test plan.
>
> Free to try 3/day. $9/mo unlimited.
>
> YOUR_URL
>
> If you're an SDET or QA lead drowning in test case backlogs — try it,
> break it, tell me what's missing. This was built because I needed it,
> so features that make it actually useful will ship first.

---

## Week 2 — Cold outreach to 50 SDET managers / QA leads

Tool for finding leads: LinkedIn Sales Navigator free trial, filter by
title = "SDET Manager" OR "QA Lead" OR "Head of QA", seniority = Manager+,
company size = 50-500 (sweet spot — big enough to have QA, small enough
to make buying decisions fast).

### Template — cold email

Subject: `fixing the worst part of writing test cases`

> Hey {FirstName},
>
> You probably spend a bigger chunk of your week turning feature specs
> into test cases than you'd like. I built a tool that does the first
> draft for you.
>
> Paste the spec → 15–25 structured test cases → export to Jira or Xray.
> Or upload screenshots and it reads the UI directly.
>
> Free tier is 3 generations/day, no card. If your team does more, it's
> $9/mo unlimited.
>
> YOUR_URL
>
> If this is useful, I'd love 10 minutes of your feedback — what's
> missing for it to be a daily tool for your team? What integration
> matters most (TestRail? Xray? GitHub Actions)?
>
> — {YourName}

**Rules for cold outreach:**
- Send to 10–15/day max, not 50 at once. You'll get marked as spam.
- Personalize the first line by skimming their recent LinkedIn activity.
- Reply to anyone who bites within 1 business day.
- Don't follow up more than twice. Move on.

### Template — LinkedIn DM (after connection accept)

> Thanks for connecting, {FirstName}. Noticed you run QA at {Company}.
> Built a small tool that turns feature specs into test case
> drafts — covers happy path, edge, negative, security, a11y and
> exports to Jira/Xray. YOUR_URL if useful. Happy to trade notes on
> what test case generation looks like on your team.

---

## Week 3 — Product Hunt launch

Launch day: Tuesday, Wednesday, or Thursday. Post at 12:01 AM PST.

### Listing

- **Tagline** (60 chars max): `AI test case generator for SDETs. Paste a spec → 15 tests.`
- **Description**:
  > QA Test Case Generator turns feature specs into paying-grade test
  > cases. Paste a feature description, upload screenshots of your app,
  > or crawl a public URL — get 15–25 structured test cases covering
  > happy paths, edge cases, negatives, security, and accessibility.
  > Export to Jira, Xray, TestRail, or push directly via API.
  >
  > Built for SDETs and QA leads tired of writing the first 15 tests
  > by hand. Free tier: 3 generations/day. Pro: $9/mo unlimited.
- **Topics**: Developer Tools, SaaS, Artificial Intelligence, Productivity.
- **First comment** (as maker):
  > Hi — maker here. Built this because the boring part of QA is writing
  > the first 15 obvious test cases — happy path, empty inputs,
  > boundaries, common attacks. Using Claude Opus 4.7 under the hood.
  > Paste your weirdest feature spec and tell me what it gets wrong.

### Pre-launch checklist (do the week before)
- [ ] Add a Product Hunt follower on your profile.
- [ ] DM 10 people who follow you asking them to upvote launch day.
- [ ] Schedule 3 Twitter posts for launch day at 12:01 AM, 8 AM, and 6 PM PST.
- [ ] Have a demo GIF ready (use Cleanshot, Kap, or Loom).

---

## Always-on — content loop (pick 1, do it weekly)

Pick one and commit to 12 weeks. Consistency > variety.

### Option A — Weekly "weird test case" thread
Every Wednesday, post a thread:
> Gave the test generator this feature spec:
> [paste]
>
> Here's what it caught that I wouldn't have:
> • [interesting test 1]
> • [interesting test 2]
> • [interesting test 3]
>
> Try it yourself: YOUR_URL

### Option B — SEO landing pages (long-term compounding)
One page per week, ~800 words each:
1. "testRigor alternative for AI test case generation"
2. "Xray test case generator for Jira Cloud"
3. "TestRail CSV import: generate test cases automatically"
4. "How to write test cases from a Figma screenshot"
5. "GitHub Actions step to generate test cases from a PR description"

These take longer to pay off (3–6 months) but compound.

### Option C — YouTube demo videos
Every Friday, post a 60-second video:
- Week 1: "Generating test cases from a checkout flow screenshot"
- Week 2: "Pushing 20 test cases straight into Jira"
- Week 3: "Crawling a competitor's site to plan tests"
- Week 4: "Editing a generated test case — manual + AI regenerate"

Post to YouTube Shorts, TikTok, Twitter/X, LinkedIn.

---

## Pricing experiments (after first 10 paying customers)

You shipped with $9/mo solo tier. Once you have 10 paying customers, start
testing:

- $19/mo "Pro" with priority access + higher screenshot limit.
- $49/mo "Team" with 5 seats + direct Jira/Xray push (currently free, make
  it a Team feature).
- Custom Enterprise with SSO + self-host option (ask directly: "I'm at
  {bigco}, we'd pay for this if it had SSO").

Don't raise prices until you have social proof (testimonials, logos) to
justify the higher bar.

---

## Metrics to track (manual spreadsheet is fine for the first 100)

| Metric | Target by week 4 | By week 12 | By week 26 |
|---|---|---|---|
| Unique visitors | 500 | 3,000 | 10,000 |
| Free-tier sign-ups (first generation) | 100 | 600 | 2,000 |
| Paying customers | 2 | 30 | 250 |
| MRR | $18 | $270 | $2,250 |

If by week 6 you don't have a single paying customer, the product isn't the
blocker — the distribution is. Stop building, go do cold outreach and Reddit
comments full-time for a week.
