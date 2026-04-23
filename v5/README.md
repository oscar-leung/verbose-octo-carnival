# v5 — LinkedIn Scraper (Playwright)

A full Playwright (Node.js) rewrite of the v4 Python/Selenium LinkedIn
scraper (`035_linkedin_easy_apply_pa.py`). Same job discovery + filter +
output semantics, but with a smarter anti-detection context and a
modular library so other platforms (Handshake, Indeed, Greenhouse) can
plug into the same output pipeline later.

## Layout

```
v5/
├── linkedin_scraper.mjs   # entry — CLI, main loop, login, scrape, save
└── lib/
    ├── config.mjs         # env + KEYWORDS + TITLE_EXCLUDE + LOCATIONS + URL builder
    ├── stealth.mjs        # stealth BrowserContext, init script, UA rotation, storageState
    ├── human.mjs          # humanWait / humanType / humanMoveTo / sessionBreak
    ├── selectors.mjs      # every LinkedIn DOM selector in one place
    └── output.mjs         # RunOutput: jobs.json + jobs.csv + jobs.jsonl + gmass_contacts.csv
```

## Install

```bash
npm install
npx playwright install chromium
```

`.env` (at repo root):

```
LINKIN_USERNAME=you@example.com
LINKIN_PASSWORD=...
```

## Run

Scrape-only (safe default — no applications submitted):

```bash
npm run v5:scrape
```

First run headed so you can solve any captcha / 2FA once — session is
saved to `~/.cache/verbose-octo-carnival/linkedin_state.json` and reused:

```bash
npm run v5:scrape:headed
```

Common flags:

```bash
node v5/linkedin_scraper.mjs \
  --keyword="SDET" \
  --location="Remote" \
  --max-jobs=50 \
  --verbose
```

| Flag | Meaning |
|------|---------|
| `--dry-run` | Scrape only — default behaviour |
| `--apply` | Open Easy Apply modal (currently opens + dismisses; FSM port is tracked for v6) |
| `--headed` | Visible browser |
| `--max-jobs=N` | Cap total scraped jobs across all keywords |
| `--keyword="..."` | Override keyword list with a single keyword |
| `--location="..."` | Override location list with a single location |
| `--pages-per-keyword=N` | Pagination depth (default 2) |
| `--storage=<path>` | Custom storageState JSON path |
| `--verbose` | Log every skipped job |

## Output

Each run produces a timestamped folder:

```
runs/linkedin_v5_2026-04-23-05-50-12/
├── run.log              # timestamped log lines (also to stdout)
├── jobs.jsonl           # streaming record file (crash-safe)
├── jobs.json            # final pretty-printed array
├── jobs.csv             # all records, JobRecord schema
├── gmass_contacts.csv   # rows with scraped recruiter emails (GMass import)
└── storage_state.json   # cookies + localStorage for next run
```

CSV schema matches the v4 `library/gsheets.py` column order so an
existing Google Sheets sync can consume v5 output unchanged.

## Anti-detection upgrades over v4

v4 set four Chromium flags and a single CDP line
(`navigator.webdriver → undefined`). v5's `launchStealthContext` adds:

1. **Modern UA rotation** with matching `sec-ch-ua` / `sec-ch-ua-platform` client hints (Chrome 128–129 on macOS/Windows).
2. **`addInitScript` patches before any page JS runs**: `navigator.webdriver`, `navigator.plugins` (3-entry array), `navigator.languages`, `window.chrome` (runtime/loadTimes/csi/app), `permissions.query('notifications')`, `WebGLRenderingContext.getParameter` vendor/renderer spoof, `hardwareConcurrency`, `deviceMemory`.
3. **Randomized viewport + timezone + deviceScaleFactor** per run.
4. **`storageState` reuse** — first successful login is the only one; subsequent runs restore cookies so LinkedIn sees a returning session instead of a fresh automation fingerprint.
5. **Human-paced interaction**: per-keystroke jitter, bezier-ish mouse paths, incremental scroll with 280–520px deltas + 350–900ms pauses, and the same post-apply cooldowns as v4 (8–18s per apply, 60–120s every 4 applies).

## What's intentionally out of scope for v5

- **Easy Apply modal FSM** — the 20-step modal walker from v4
  (`advance_modal()` at line 407 onwards, plus the work-auth / voluntary
  ID / city autocomplete handlers) is not yet ported. `--apply` opens
  the dialog, snapshots it, then discards. Status recorded is `dry_run`.
- **Google Sheets sync** — `library/gsheets.py` is still Python; v5's
  CSV uses the same column order so piping stays trivial.
- **Handshake / Indeed / Greenhouse** — each has its own v4 script;
  migrating them is a follow-up that can reuse `lib/stealth.mjs`,
  `lib/human.mjs`, and `lib/output.mjs` unchanged.

## Validate without running

```bash
npm run v5:check   # node --check each module
```
