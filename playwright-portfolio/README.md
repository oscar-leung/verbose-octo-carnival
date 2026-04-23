# playwright-portfolio — SDET Test Automation Framework

A production-shaped Playwright + TypeScript test framework exercised against two live public systems under test:

- **E2E UI** — [`saucedemo.com`](https://www.saucedemo.com) (Sauce Labs' public training app)
- **API** — [`jsonplaceholder.typicode.com`](https://jsonplaceholder.typicode.com) (public REST sandbox)

Built to show the patterns hiring managers actually look for: Page Object Model, typed fixtures, tagged suites, cross-browser + mobile projects, API + UI under one runner, and CI artifacts (HTML report, JUnit, traces, videos, screenshots).

---

## Why this framework

| Concern | How it's handled |
|---|---|
| Flaky waits | Playwright auto-waiting + web-first assertions. No `sleep`s. |
| Locator drift | `data-test` attributes first; semantic `getByRole` second. |
| Test setup | Typed fixtures (`authedInventoryPage`) keep specs free of boilerplate login. |
| Test pyramid | API project executes first in CI; UI runs in parallel across 3 browsers. |
| Debugging | `trace: retain-on-failure`, `video: retain-on-failure`, JUnit + HTML report. |
| Secrets | Baseline URL + API keys pulled from env (`BASE_URL`). |
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
│   │   ├── login.page.ts
│   │   ├── inventory.page.ts
│   │   ├── cart.page.ts
│   │   └── checkout.page.ts
│   ├── fixtures/
│   │   └── auth.fixture.ts       # `test` extended with page-object fixtures
│   ├── data/
│   │   ├── users.ts              # canned saucedemo user matrix
│   │   └── products.ts
│   ├── e2e/                      # 21 UI tests × 3 browsers
│   │   ├── login.spec.ts
│   │   ├── inventory.spec.ts
│   │   ├── cart.spec.ts
│   │   └── checkout.spec.ts
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
npm run typecheck          # tsc --noEmit
```

Override the SUT:

```bash
BASE_URL=https://staging.example.com npm test
```

---

## Test coverage snapshot

**UI (saucedemo.com)** — 21 tests × 3 desktop browsers = 63 runs

- **Authentication** — happy path, locked-out user, missing username, missing password, invalid credentials, logout
- **Inventory** — product count, A→Z / Z→A sort, price low→high / high→low sort, add-to-cart badge, remove-from-cart badge
- **Cart** — items persist from inventory, remove-in-cart updates badge, continue-shopping returns to inventory, empty cart state
- **Checkout** — happy-path order with subtotal + tax = total assertion, required first name, required last name, required postal code

**API (jsonplaceholder.typicode.com)** — 7 tests

- `GET /users` full list with schema assertions on each user
- `GET /users/:id` single user
- `GET /users/:id` → 404 for unknown ids
- `GET /posts?userId=1` filter by relation
- `POST /posts` create with body echo + generated `id`
- `PUT /posts/:id` replace
- `DELETE /posts/:id` → 200

**Tags**: `@smoke` (critical path), `@regression` (full suite), `@api`, `@mobile` (reserved for the `mobile-chrome` project).

---

## Design choices worth calling out

1. **POM via classes, not functions.** Constructors wire locators once; methods describe user intent (`addToCart`, `checkout`, `fillInfo`) rather than clicks. Cheap to scan, cheap to diff.
2. **`data-test` locators first.** saucedemo publishes them; using them survives style refactors. Fallback is `getByRole`.
3. **Fixtures over `beforeEach`.** `authedInventoryPage` is a composable fixture — any test that asks for it gets a logged-in session with no boilerplate.
4. **Projects, not forks.** A single config runs UI across three browsers *and* the API suite, with per-project `testDir` and `baseURL`.
5. **CI does the real work.** Local dev prefers `chromium` + no retries; CI enables `retries: 2`, `workers: 2`, and forbids `test.only` leaking in.
6. **Traces on failure only.** `retain-on-failure` avoids the multi-GB trace dumps that kill a CI bucket, while still giving you `npx playwright show-trace` when something breaks.

---

## CI

`.github/workflows/playwright.yml` runs a matrix of `{chromium, firefox, webkit, api}` on every push and PR that touches `playwright-portfolio/`. Artifacts uploaded per-job:

- `playwright-report-<project>` — always (open with `npm run report`)
- `test-results-<project>` — on failure (traces, videos, screenshots)

---

## Extending

- **New page** — add a class under `tests/pages/`, register it in `tests/fixtures/auth.fixture.ts` if you want it injected.
- **New user** — add to `tests/data/users.ts` (typed via `satisfies`).
- **Mobile test** — tag with `@mobile`; the `mobile-chrome` project picks it up automatically.
- **Visual regression** — `await expect(page).toHaveScreenshot()` is already available; snapshots will land under `tests/e2e/__screenshots__/` when you add them.

---

## Notes

- The sibling `qa_portfolio/` directory in this repo is the Selenium + pytest counterpart to this framework, same SUT — useful for a before/after comparison of the two dominant UI automation stacks.
- The API suite targets JSONPlaceholder because it's the most stable public REST sandbox available — no API key, no rate ceiling for CI volumes, no schema drift.
