// v5/lib/selectors.mjs — every LinkedIn DOM selector v5 touches, in one place.
//
// Ported from 035_linkedin_easy_apply_pa.py. Kept as Playwright-friendly
// strings (CSS where possible, XPath prefixed with "xpath=" for Locator).
// When LinkedIn re-skins, this is the only file that should need updating.

export const LOGIN = {
  url: 'https://www.linkedin.com/login',
  // Fallback chain — LinkedIn has shipped three login-form variants.
  emailCandidates: [
    '#username',
    'input[name="session_key"]',
    'input[type="email"]',
    'input[autocomplete="username"]',
    'xpath=(//input[@type="text"])[1]',
    'xpath=(//input)[1]',
  ],
  passwordCandidates: [
    'input[type="password"]',
    '#password',
    'input[autocomplete="current-password"]',
  ],
  submitCandidates: [
    'button[type="submit"]',
    'button[data-litms-control-urn="login-submit"]',
  ],
  feedCheckUrlFragments: ['/feed', '/checkpoint', '/jobs'],
};

export const SEARCH = {
  jobCard: 'xpath=//li[@data-occludable-job-id]',
  jobCardJobIdAttr: 'data-occludable-job-id',
  jobCardTitle:
    'xpath=.//a[contains(@class,"job-card-container__link")]',
  jobCardCompany:
    'xpath=.//span[contains(@class,"job-card-container__primary-description") or contains(@class,"job-card-container__company-name")]',
  jobCardLocation:
    'xpath=.//li[contains(@class,"job-card-container__metadata-item")]',
};

export const JOB_DETAIL = {
  descriptionCandidates: [
    'div.jobs-description__content',
    '#job-details',
    'article.jobs-description',
  ],
  postedAgoCandidates: [
    'span.jobs-unified-top-card__posted-date',
    'span.tvm__text--neutral',
    'span.jobs-unified-top-card__subtitle-secondary-grouping > span',
  ],
};

export const APPLY = {
  easyBtn: '#jobs-apply-button-id',
  nextBtn: 'button[aria-label="Continue to next step"]',
  reviewBtn: 'button[aria-label="Review your application"]',
  submitBtn: 'button[aria-label="Submit application"]',
  dismissBtn: 'button[aria-label="Dismiss"]',
  doneBtn: 'button[aria-label="Done"]',
  modalHeading: 'xpath=//div[@data-test-modal]//h3',
  discardConfirm:
    'xpath=//div[@role="alertdialog"]//button[@data-control-name="discard_application_confirm_btn"]',
};

/** Try each candidate selector; return the first Locator whose count() > 0.
 *  Returns null if none match within timeout. */
export async function firstVisible(page, candidates, { timeout = 3000 } = {}) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    for (const sel of candidates) {
      const loc = page.locator(sel).first();
      try {
        if ((await loc.count()) > 0 && (await loc.isVisible())) return loc;
      } catch {
        // ignore, try next
      }
    }
    await new Promise((r) => setTimeout(r, 150));
  }
  return null;
}
