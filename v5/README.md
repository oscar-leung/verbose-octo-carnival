# v5 — LinkedIn Scraper (Playwright)

A full Playwright (Node.js) rewrite of the v4 Python/Selenium LinkedIn
scraper (`035_linkedin_easy_apply_pa.py`). Feature-complete: job
discovery, title filter, Easy Apply modal FSM, output pipeline, and
Google Sheets sync — all in Node, with smarter anti-detection.

## Layout

```
v5/
├── linkedin_scraper.mjs   # entry — CLI, main loop, login, scrape, apply, save, sync
└── lib/
    ├── config.mjs         # env + KEYWORDS + TITLE_EXCLUDE + LOCATIONS + URL builder
    ├── stealth.mjs        # stealth BrowserContext, init script, UA rotation, storageState
    ├── human.mjs          # humanWait / humanType / humanMoveTo / sessionBreak
    ├── selectors.mjs      # every LinkedIn DOM selector in one place
    ├── apply_modal.mjs    # Easy Apply modal FSM (work auth, voluntary ID, city, etc.)
    ├── output.mjs         # RunOutput: jobs.json + jobs.csv + jobs.jsonl + gmass_contacts.csv
    └── gsheets.mjs        # Google Sheets sync (port of library/gsheets.py)

tests/
└── v5_smoke.test.mjs      # node --test unit tests (9 passing)
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
| `--dry-run` | Scrape only — default behaviour (no applications submitted) |
| `--apply` | Drive the Easy Apply modal FSM and submit applications |
| `--headed` | Visible browser |
| `--max-jobs=N` | Cap total scraped jobs across all keywords |
| `--max-applies=N` | Cap submissions per session (default 8) |
| `--keyword="..."` | Override keyword list with a single keyword |
| `--location="..."` | Override location list with a single location |
| `--pages-per-keyword=N` | Pagination depth (default 2) |
| `--storage=<path>` | Custom storageState JSON path |
| `--no-sheet-sync` | Skip Google Sheets append (always skipped if env vars unset) |
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

## Easy Apply modal FSM

`lib/apply_modal.mjs` ports v4's `advance_modal()` walker. Per step it
reads the modal heading and dispatches a handler:

| Heading match | Handler |
|---------------|---------|
| Privacy policy | clicks "I Agree Terms & Conditions" |
| Additional Questions | fills `1` for inputs, `Yes` for selects, then runs work-auth |
| Work authorization | radio answers from `WORK_AUTH_ANSWERS`, dropdown fallback |
| Voluntary self identification | gender, race, veteran, disability, name, date |
| Resume | sets the LinkedIn URL field |

City autocomplete (`#city-HOME-CITY`) runs on every step as a fallback.
Advance order: **Review → Submit → Next**. On any error or after 20
steps, the modal is force-dismissed (Dismiss + Discard confirm).

## Google Sheets sync

If `GOOGLE_SERVICE_ACCOUNT_JSON` and `GOOGLE_SHEET_ID` are set in `.env`,
the run-end pipeline appends new rows to the `Applications` tab using
the same `platform|job_id` dedupe as v4's `library/gsheets.py`. The tab
is auto-created with the COLUMNS header if missing. Pass
`--no-sheet-sync` to skip even when configured.

## Tests

```bash
npm test          # 9 unit tests, ~110ms
npm run v5:check  # node --check on every module
```

## Future work (not blocking v5)

- **Handshake / Indeed / Greenhouse** Playwright ports — reuse
  `lib/stealth.mjs`, `lib/human.mjs`, `lib/output.mjs`, and
  `lib/gsheets.mjs` unchanged. Each platform needs its own
  `selectors.mjs` + login flow.
