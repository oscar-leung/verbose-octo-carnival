# FEEDBACK.md — Serifu feedback ledger

Single source of truth for user reports. One row per report. Maintained by
`feedback-triage` (.claude/agents/feedback-triage.md).

**How feedback gets added**
- Sources: Oscar's in-session directives (source=owner), friends/testers,
  store reviews, and GitHub issues on `oscar-leung/verbose-octo-carnival`.
  Triage sweeps check open GitHub issues; real user-facing feedback gets a
  row here (with the issue number in Source), non-feedback issues (chores,
  CI, refactors) are noted as not-feedback and left in GitHub.
- Verbatim first: record what was actually said (short quote), then the
  interpretation. Never invent feedback that wasn't given.
- Route, don't fix: bugs → frontend-dev/backend-dev; confusing screens →
  ux-designer; content gaps → content-writer; pricing → biz-strategist;
  store-review issues → store-ops. Routed tasks must be actionable without
  reading this whole ledger.
- **Three-similar-reports rule:** one report is a data point, not a trend;
  three similar reports = a priority — escalate to chief-of-staff.
- Close the loop: when a fix ships, mark the row `shipped` with the PR and
  what to tell the reporter. Declining is allowed with the reason on record.
- Severity: `blocker` (can't use the app) / `friction` (works but hurts) /
  `wish` (nice-to-have).

**GitHub issues check (2026-09-03):** queried open and closed issues on
`oscar-leung/verbose-octo-carnival` — none found via the GitHub API, so no
issue-sourced rows yet. Re-check on each triage sweep.

## Ledger

| # | Source | Date | Verbatim (short) | Interpretation | Severity | Owner agent | Status |
|---|--------|------|------------------|----------------|----------|-------------|--------|
| 1 | owner (Oscar Leung, session) | 2026-08 | "There's too much text. Can you simplify it even more?" | Landing/demo pages are copy-heavy; cut to essentials. | friction | content-writer + frontend-dev | shipped — landing copy cut to essentials (PR #25). Tell reporter: landing now shows only the core pitch and CTA. |
| 2 | owner (Oscar Leung, session) | 2026-08 | "it's too cluttered for a phone usage too much read. Make it ui ux friendly" | Room screen is unusable on phones — too many panels/text at once; needs a mobile-first layout. | friction | ux-designer → frontend-dev | shipped — three-tab mobile layout (PR #26). Tell reporter: on phones the room is now split into three tabs instead of one long scroll. |
| 3 | owner (Oscar Leung, session) | 2026-08 | "People make the 'buy me my coffee' thing too, and people like it. 5 dollar charge not good." | A $5 charge is the wrong model for this audience; prefer voluntary support (Buy Me a Coffee style). | friction | biz-strategist | shipped — donations-first plan adopted + ☕ links added (routed to biz-strategist; see docs/BUSINESS.md). Tell reporter: no paywall; support is voluntary via coffee links. |
| 4 | owner (Oscar Leung, session) | 2026-08 | "I'm not able to create a room. Why is that?" | Room creation hung at "connecting…" on the GitHub Pages static demo — no Socket.IO server exists on a static host, so rooms can never connect there. | blocker | frontend-dev | shipped — static-demo notice explains rooms need the full deployment (PR #25). Root cause on record: no server on static host. Tell reporter: use the Render deployment for rooms; the static demo is solo-practice only. |
| 5 | owner (Oscar Leung, session) | 2026-08 | iPhone speech scoring unavailable (Web Speech ja-JP not supported in iOS Safari as we use it) | Platform limitation, not a bug we can patch in-web; documented for users. Future path: native SFSpeechRecognizer plugin when we go to the App Store. | friction | store-ops + backend-dev | open / declined-for-now — reason: iOS platform limitation; revisit with SFSpeechRecognizer plugin at App Store submission. Tell reporter: iPhone users can join rooms and use manual pass; scoring needs another device for now. |
