// v5/lib/apply_modal.mjs — Easy Apply modal FSM, ported from v4.
//
// Source: 035_linkedin_easy_apply_pa.py:290–490 (advance_modal + handlers).
//
// FSM:
//   1. Click #jobs-apply-button-id.
//   2. Loop up to MODAL_MAX_STEPS:
//      a. Read modal heading (h3 inside [data-test-modal])
//      b. Dispatch a per-step handler (work_auth | voluntary_id |
//         additional_q | resume_linkedin | privacy_policy)
//      c. Always run fillHomeCity() as a belt-and-suspenders fallback —
//         the city autocomplete shows up on multiple steps.
//      d. Resolve advance button: review → submit → next.
//   3. On failure: emergencyClose() (dismiss → discard confirm).
//
// Returns one of: 'applied' | 'skipped' | 'error' | 'dry_run'.

import { humanWait, sleep } from './human.mjs';
import { APPLY } from './selectors.mjs';

const MODAL_MAX_STEPS = 20;

const WORK_AUTH_ANSWERS = [
  { text: 'Will you now, or in the future, require sponsorship for employment visa status', answer: 'No' },
  { text: 'Are you legally authorized to work in the United States', answer: 'Yes' },
  { text: 'Are you willing to take a drug test', answer: 'Yes' },
  { text: "Are you comfortable commuting to this job's location?", answer: 'Yes' },
  { text: 'Are you comfortable working in a remote setting?', answer: 'Yes' },
  { text: 'How did you hear about this job?', answer: 'LinkedIn' },
  { text: 'What is your target salary range?', answer: '100k-110k' },
];

/** XPath string-literal escape (matches v4's xpath_literal). */
function xpathLit(s) {
  if (!s.includes("'")) return `'${s}'`;
  if (!s.includes('"')) return `"${s}"`;
  const parts = s.split("'");
  return 'concat(' + parts.map((p) => `'${p}'`).join(',"\'",') + ')';
}

async function locVisible(page, selector) {
  const loc = page.locator(selector).first();
  if ((await loc.count()) === 0) return null;
  try {
    if (await loc.isVisible()) return loc;
  } catch {}
  return null;
}

async function safeClick(page, selector, { timeout = 4000 } = {}) {
  const loc = page.locator(selector).first();
  try {
    await loc.scrollIntoViewIfNeeded({ timeout });
    await loc.click({ timeout });
    await humanWait(0.3, 0.8);
    return true;
  } catch {
    return false;
  }
}

async function modalHeading(page) {
  const loc = page.locator(APPLY.modalHeading).first();
  try {
    if ((await loc.count()) > 0) return ((await loc.innerText()) || '').trim();
  } catch {}
  return '';
}

// ── Step handlers ───────────────────────────────────────────────────────────

async function fillWorkAuth(page) {
  for (const q of WORK_AUTH_ANSWERS) {
    // Try radio first (the common case).
    const radio = `xpath=//fieldset[.//legend[contains(normalize-space(.), ${xpathLit(q.text)})]]//label[@data-test-text-selectable-option__label=${xpathLit(q.answer)}]`;
    if (await safeClick(page, radio, { timeout: 1500 })) continue;

    // Dropdown fallback: find the label, follow its `for=` to a <select>.
    try {
      const labelLoc = page.locator(`xpath=//label[contains(normalize-space(.), ${xpathLit(q.text)})]`).first();
      if ((await labelLoc.count()) === 0) continue;
      const forId = await labelLoc.getAttribute('for');
      if (!forId) continue;
      await page.locator(`select#${CSS.escape(forId)}`).first().selectOption({ label: q.answer });
    } catch { /* skip */ }
  }
}

async function fillVoluntarySelfId(page, profile) {
  for (const [label, value] of [
    ['Gender', 'Male'],
    ['Race/Ethnicity', 'Asian (Not Hispanic or Latino)'],
  ]) {
    try {
      const sel = page.locator(
        `xpath=//label[.//strong[normalize-space()=${xpathLit(label)}]]/following::select[1]`,
      ).first();
      if ((await sel.count()) > 0) await sel.selectOption({ label: value });
    } catch { /* ignore */ }
  }
  for (const [optText, xp] of [
    ['I am not a protected veteran',
      "(//select[.//option[normalize-space()='I am not a protected veteran']])[1]"],
    ['No, I do not have a disability and have not had one in the past',
      "(//select[.//option[normalize-space()='No, I do not have a disability and have not had one in the past']])[1]"],
  ]) {
    try {
      const sel = page.locator(`xpath=${xp}`).first();
      if ((await sel.count()) > 0) await sel.selectOption({ label: optText });
    } catch { /* ignore */ }
  }
  // Name + date inputs (some job postings include them).
  try {
    const nameInp = page.locator("xpath=//label[normalize-space()='Your Name']/following::input[1]").first();
    if ((await nameInp.count()) > 0) {
      await nameInp.fill('');
      await nameInp.fill(profile.fullName);
    }
  } catch { /* ignore */ }
  try {
    const dateInp = page.locator("xpath=//label[normalize-space()=\"Today's Date\"]/following::input[1]").first();
    if ((await dateInp.count()) > 0) {
      const d = new Date();
      const stamp = `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}/${d.getFullYear()}`;
      await dateInp.fill('');
      await dateInp.fill(stamp);
    }
  } catch { /* ignore */ }
}

async function fillAdditionalQuestions(page, profile) {
  // Generic catch-all: each question lives in div.ph5 > div:nth-child(1) > div.
  const boxes = page.locator("xpath=//div[@class='ph5']/div[1]/div");
  const count = await boxes.count();
  for (let i = 0; i < count; i++) {
    const box = boxes.nth(i);
    const inp = box.locator('xpath=.//input').first();
    if ((await inp.count()) > 0) {
      try { await inp.fill('1'); } catch {}
    }
    const sel = box.locator('xpath=.//select').first();
    if ((await sel.count()) > 0) {
      try { await sel.selectOption({ label: 'Yes' }); } catch {}
    }
  }
  // Work-auth questions sometimes appear under "Additional Questions" too.
  await fillWorkAuth(page);
}

async function fillHomeCity(page, profile) {
  const inp = page.locator("xpath=//input[contains(@id,'city-HOME-CITY')]").first();
  if ((await inp.count()) === 0) return;
  try {
    await inp.fill(profile.homeCity);
    await sleep(800);
    await inp.press('ArrowDown');
    await inp.press('Enter');
    await sleep(500);
  } catch { /* ignore */ }
}

async function fillResumeLinkedIn(page, profile) {
  const inp = page.locator(
    'xpath=//div[@data-test-single-line-text-form-component][.//label[normalize-space()="LinkedIn"]]//input',
  ).first();
  if ((await inp.count()) === 0) return;
  try {
    await inp.fill('');
    await inp.fill(profile.linkedinUrl);
  } catch { /* ignore */ }
}

async function fillPrivacyPolicy(page) {
  await safeClick(
    page,
    'xpath=//label[@data-test-text-selectable-option__label="I Agree Terms & Conditions"]',
  );
}

const STEP_HANDLERS = [
  ['privacy policy', fillPrivacyPolicy],
  ['additional questions', fillAdditionalQuestions],
  ['work authorization', fillWorkAuth],
  ['voluntary self identification', fillVoluntarySelfId],
  ['resume', fillResumeLinkedIn],
];

// ── FSM core ────────────────────────────────────────────────────────────────

async function emergencyClose(page) {
  await safeClick(page, APPLY.dismissBtn, { timeout: 2000 });
  await sleep(400);
  await safeClick(page, APPLY.discardConfirm, { timeout: 2000 });
}

async function dismissPostApply(page) {
  for (const sel of [APPLY.dismissBtn, APPLY.doneBtn]) {
    if (await safeClick(page, sel, { timeout: 3000 })) return;
  }
}

/**
 * Run one modal step: dispatch handler, then click the right advance button.
 * @returns {Promise<{submitted: boolean}>}
 * @throws {Error} when no advance button is found.
 */
async function advanceModal(page, profile, log) {
  const heading = (await modalHeading(page)).toLowerCase();
  for (const [needle, handler] of STEP_HANDLERS) {
    if (heading.includes(needle)) {
      try {
        await handler(page, profile);
      } catch (e) {
        log.warn(`    handler "${needle}": ${e.message}`);
      }
      break;
    }
  }
  // Belt-and-suspenders: city autocomplete can appear on any step.
  await fillHomeCity(page, profile);

  if (await locVisible(page, APPLY.reviewBtn)) {
    await safeClick(page, APPLY.reviewBtn);
    await humanWait(0.5, 1.2);
    if (await locVisible(page, APPLY.submitBtn)) {
      await safeClick(page, APPLY.submitBtn);
      await dismissPostApply(page);
      return { submitted: true };
    }
    return { submitted: false };
  }
  if (await locVisible(page, APPLY.submitBtn)) {
    await safeClick(page, APPLY.submitBtn);
    await dismissPostApply(page);
    return { submitted: true };
  }
  if (await locVisible(page, APPLY.nextBtn)) {
    await safeClick(page, APPLY.nextBtn);
    return { submitted: false };
  }
  throw new Error('No advance button found');
}

/**
 * Drive the Easy Apply modal to completion.
 *
 * @param {import('playwright').Page} page
 * @param {object} opts
 * @param {object} opts.profile          { fullName, linkedinUrl, homeCity }
 * @param {boolean} [opts.dryRun]        if true, opens modal then dismisses
 * @param {object} opts.log              has .info/.warn/.error
 * @returns {Promise<{status: string, note: string}>}
 */
export async function runEasyApply(page, opts) {
  const { profile, dryRun = false, log } = opts;
  if (!(await safeClick(page, APPLY.easyBtn))) {
    return { status: 'skipped', note: 'no_easy_apply_button' };
  }
  await humanWait(1, 2);

  if (dryRun) {
    await emergencyClose(page);
    return { status: 'dry_run', note: 'dry_run_close' };
  }

  for (let step = 1; step <= MODAL_MAX_STEPS; step++) {
    try {
      const { submitted } = await advanceModal(page, profile, log);
      if (submitted) {
        log.info(`    applied (step ${step})`);
        return { status: 'applied', note: `submitted_step_${step}` };
      }
      await humanWait(0.5, 1.5);
    } catch (e) {
      if (/No advance button/.test(e.message)) {
        log.warn(`    stuck at step ${step}: ${e.message}`);
      } else {
        log.error(`    modal error step ${step}: ${e.message}`);
      }
      await emergencyClose(page);
      return { status: 'error', note: `step_${step}:${e.message.slice(0, 80)}` };
    }
  }
  log.warn(`    exceeded ${MODAL_MAX_STEPS} steps — aborting`);
  await emergencyClose(page);
  return { status: 'error', note: 'max_steps_exceeded' };
}
