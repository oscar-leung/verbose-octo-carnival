# Prompt Eval Checklist

Run the 4 built-in samples (Password reset, Checkout + payment, Profile
photo upload, Rate-limited API). For each one, read the output and grade
it against the checklist below. A single ✗ on a "blocker" row means the
prompt still needs tuning.

| # | Check | Blocker? | Why |
|---|---|---|---|
| 1 | **Title describes behavior, not category.** Bad: "Negative email test". Good: "Blank email shows 'Required' inline error". | ✅ | Customers read titles first; vague titles = distrust. |
| 2 | **Expected result is specific.** Bad: "Error is shown". Good: "Page displays exact text 'Please enter a valid email address' below the Email input; Submit button disabled." | ✅ | Entire product value is in this field. |
| 3 | **Preconditions include concrete test data.** Bad: "User is logged in". Good: "Authenticated as email='primary+test@example.com', role='customer', failed_login_attempts_last_hour=0". | ✅ | Without data, the test isn't independently runnable. |
| 4 | **Steps are atomic.** Bad: "Click Submit and verify error". Good: `["Click 'Submit'"]` + the verify goes into expected_result. | ✅ | Atomic steps map 1:1 to automation. |
| 5 | **Boundary tests hit limit, limit+1, limit-1.** For "5 failed attempts locks the account": check tests for 4th (not locked), 5th (not locked), 6th (locked). | ✅ | Classic off-by-one zone. |
| 6 | **At least one unicode / long-string test per free-text field.** | ✗ | Nice-to-have on v1, must-have on v2. |
| 7 | **Security tests use real attack strings** (`"' OR 1=1 --"`, `"<script>alert(1)</script>"`), not placeholders. | ✗ | Differentiates us from generic test-case templates. |
| 8 | **Accessibility tests cite WCAG criteria** ("contrast ratio >= 4.5:1", "keyboard-only navigation reaches every interactive element"). | ✗ | SDETs working in regulated industries care. |
| 9 | **Count: 8-25 tests total.** Simple specs ~= 10. Complex specs ~= 20+. | ✗ | Under 8 feels lazy; over 25 feels padded. |
| 10 | **No hallucinated UI elements** when screenshots are provided. | ✅ | One fake button = whole feature loses trust. |

## Running the samples

1. `npm run dev`
2. Set `ANTHROPIC_API_KEY` in `.env.local`.
3. Open http://localhost:3000 and click each sample chip in turn.
4. Read the 10-20 generated test cases per sample against the checklist.
5. If any blocker-row check fails on >= 2 of 4 samples, tune
   `SYSTEM_PROMPT` / `TEST_CASE_SCHEMA` descriptions in
   `app/api/generate/route.ts` and repeat.

## Spot-check specifics by sample

**Password reset** — look for:
- `high` priority on reset-link expiry and account-lockout tests
- Off-by-one on 5 failed attempts (4th, 5th, 6th)
- 15-minute link expiry boundary (14 min, 15 min, 15 min 1 s)
- Complexity rules: 11-char password rejected, 12-char accepted, missing uppercase/number/symbol rejected
- First-use expiry: reset link works once, second use shows expired page
- Locked-account behavior: receive email but get "contact support" page on link click

**Checkout + payment** — look for:
- 15-minute inventory hold boundary
- Payment failure returns to payment step (not cart)
- Guest vs authenticated checkout paths
- Shipping method price variants ($5 / $12 / $25)
- Card validation (expired, insufficient funds, invalid CVV)
- Cart-persists-30-days edge (day 29 vs day 31)

**Profile photo upload** — look for:
- Exact 5MB boundary (5MB - 1 byte, 5MB, 5MB + 1 byte)
- Format rejection strings (GIF, SVG, BMP)
- Resize verification (512×512 exact dimensions)
- Anonymous user sign-in prompt path
- Existing-photo-retained-on-failure behavior
- Cross-platform (web / iOS / Android)

**Rate-limited API** — look for:
- 60 req/min boundary: 60th succeeds, 61st 429
- Retry-After header on 429
- X-Request-Id header present on all responses
- Body length: 2000 chars succeeds, 2001 returns 413
- Auth variants: missing token / invalid token / valid token but missing scope
- Concrete attack strings in security tests

## If quality is still not paying-grade after tuning

Next levers to try, in order:
1. Add 1-2 worked examples at the end of the system prompt (showing ideal title / expected_result / preconditions for one test case each).
2. Add a verification pass — run the output back through Claude with "grade this against the checklist and fix anything that doesn't meet the bar".
3. Try `output_config.effort = "max"` is already set; no further lever here without a model change.
4. Switch to a two-call pipeline: first call generates test case IDs + titles only, second call expands each into full detail. Slower but gives each test case more attention.
