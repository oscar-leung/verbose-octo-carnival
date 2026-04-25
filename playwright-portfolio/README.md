# playwright-portfolio — SDET Test Automation Framework

A production-shaped Playwright + TypeScript test framework exercised against two live public systems under test:

- **E2E UI** — [`demo.playwright.dev/todomvc`](https://demo.playwright.dev/todomvc) (Playwright's reference TodoMVC, GitHub-Pages hosted, bulletproof in CI)
- **API** — [`jsonplaceholder.typicode.com`](https://jsonplaceholder.typicode.com) (public REST sandbox, no auth, no rate ceiling)

Built to show the patterns hiring managers actually look for: Page Object Model, typed fixtures, tagged suites, cross-browser + mobile projects, API + UI under one runner, and CI artifacts (HTML report, JUnit, traces, videos, screenshots).

---

## Why this framework

| Concern | How it's handled |
|---|---|
| Flaky waits | Playwright auto-waiting + web-first assertions. No `sleep`s. |
| Locator drift | `getByRole` / `getByPlaceholder` / `getByTestId` — user-facing locators that survive style refactors. |
| Test setup | Typed fixtures (`todoPage`, `seededTodoPage`) keep specs free of boilerplate. |
| Test pyramid | API project executes first in CI (no browser needed); UI runs in parallel across 3 browsers. |
| Debugging | `trace: retain-on-failure`, `video: retain-on-failure`, JUnit + HTML report. |
| Secrets / env | Baseline URL overridable via `BASE_URL` env var. |
| CI | GitHub Actions matrix across `chromium`, `firefox`, `webkit`, `api`. |

---

## Layout

```
playwright-portfolio/
├── playwright.config.ts          # projects: chromium / firefox / webkit / mobile-chrome / api
├── tsconfig.json                 # strict TS, path aliases
├── tests/
│   ├── pages/                    # Page Object Model (TypeScript classes)
│   │   ├── base.page.ts
│   │   └── todo.page.ts
│   ├── fixtures/
│   │   └── todo.fixture.ts       # `test` extended with todoPage + seededTodoPage
│   ├── data/
│   │   └── samples.ts
│   ├── e2e/                      # 15 UI tests × 3 desktop browsers + 1 mobile
│   │   ├── add.spec.ts
│   │   ├── complete.spec.ts
│   │   ├── edit.spec.ts
│   │   ├── filter.spec.ts
│   │   └── persistence.spec.ts
│   └── api/                      # 7 API tests, browser-free
│       └── jsonplaceholder.spec.ts
└── .github/workflows/playwright.yml (at repo root)
```

---

## Quickstart

```bash
cd playwright-portfolio
npm install
npx playwright install --with-deps   # first time only
npm test                              # runs everything
```

Common scripts:

```bash
npm run test:smoke         # @smoke-tagged critical path (cross-browser)
npm run test:regression    # full @regression suite
npm run test:api           # API project only (no browser needed)
npm run test:chromium      # single browser
npm run test:ui            # Playwright's time-travel UI mode
npm run test:headed        # watch it run
npm run report             # open last HTML report
npm run lint               # ESLint with eslint-plugin-playwright
npm run typecheck          # tsc --noEmit
npm run check              # typecheck + lint together (pre-commit hook material)
```

Override the SUT:

```bash
BASE_URL=https://staging.example.com/todomvc npm test
```

---

## Test coverage snapshot

**UI (TodoMVC)** — 16 tests × 3 desktop browsers; 1 also runs on the `mobile-chrome` project (Pixel 7 viewport)

- **Add** — single, multiple, input clears, counter shows remaining
- **Complete / clear** — toggle, untoggle, toggle-all, clear-completed
- **Edit / delete** — double-click to edit + Enter to save, delete button, empty-list hides main section
- **Filter** — Active / Completed / All filter links
- **Persistence + responsive** — localStorage survives reload, mobile viewport renders

**API (jsonplaceholder.typicode.com)** — 7 tests

- `GET /users` full list with per-user schema assertions
- `GET /users/:id` single user
- `GET /users/:id` → 404 for unknown ids
- `GET /posts?userId=1` filter by relation
- `POST /posts` create with body echo + generated `id`
- `PUT /posts/:id` replace
- `DELETE /posts/:id` → 200

**Tags**: `@smoke` (critical path), `@regression` (full suite), `@api`, `@mobile` (reserved for the `mobile-chrome` project).

---

## Design choices worth calling out

1. **POM via classes, not functions.** Constructors wire locators once; methods describe user intent (`add`, `toggle`, `remove`, `edit`) rather than clicks. Cheap to scan, cheap to diff.
2. **User-facing locators.** `getByPlaceholder`, `getByRole`, `getByTestId` — the locators Playwright recommends because they mirror how users (and screen readers) find things.
3. **Fixtures over `beforeEach`.** `seededTodoPage` is a composable fixture — any test that needs three pre-existing todos gets them for free with no boilerplate.
4. **Projects, not forks.** A single config runs UI across three browsers *and* the API suite, with per-project `testDir` and `baseURL`.
5. **CI does the real work.** Local dev prefers a single browser + no retries; CI enables `retries: 2`, `workers: 2`, and forbids `test.only` leaking in.
6. **Traces on failure only.** `retain-on-failure` avoids the multi-GB trace dumps that kill a CI bucket, while still giving you `npx playwright show-trace` when something breaks.

---

## CI

`.github/workflows/playwright.yml` splits into two jobs that run on every push and PR touching `playwright-portfolio/`:

- **api** — single short job (no browser install), runs the API project against JSONPlaceholder
- **e2e** — matrix of `{chromium, firefox, webkit}` with a Playwright-version-keyed browser cache so cold runs install browsers once and warm runs skip the download

The CI run uses Playwright's `github` reporter, so failures land as inline annotations on the PR diff. Artifacts uploaded per-job:

- `playwright-report-<project>` — always (open with `npm run report`)
- `test-results-<project>` — on failure (traces, videos, screenshots)

---

## Extending

- **New page** — add a class under `tests/pages/`, register it in `tests/fixtures/todo.fixture.ts` if you want it injected.
- **New sample data** — add to `tests/data/samples.ts`.
- **Mobile test** — tag with `@mobile`; the `mobile-chrome` project picks it up automatically.
- **Visual regression** — `await expect(page).toHaveScreenshot()` is already available; snapshots will land under `tests/e2e/__screenshots__/` when you add them.

---

## Notes

- The sibling `qa_portfolio/` directory in this repo is a Selenium + pytest counterpart — useful for a side-by-side of the two dominant UI automation stacks.
- TodoMVC was chosen over bespoke demo shops (saucedemo, toolshop) specifically because it's hosted on GitHub Pages with no CDN/bot-detection layer in front of it, so CI runs are deterministic. The API suite targets JSONPlaceholder for the same reason — no API key, no rate ceiling, no schema drift.
