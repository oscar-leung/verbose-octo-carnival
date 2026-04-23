#!/usr/bin/env node
// v5/linkedin_scraper.mjs — LinkedIn Jobs scraper, Playwright edition.
//
// v4 was Python/Selenium (see 035_linkedin_easy_apply_pa.py). This rewrite:
//   • Uses Playwright (Chromium) with a stealth context + storageState reuse.
//   • Default action is SCRAPE-ONLY — records job metadata + parses
//     descriptions for skills/recruiter email. Easy Apply submission is
//     gated behind --apply (off by default for safety).
//   • Writes jobs.json, jobs.csv, jobs.jsonl, gmass_contacts.csv, and a
//     storage_state.json (session cookies) under runs/linkedin_v5_<ts>/.
//
// CLI:
//   node v5/linkedin_scraper.mjs [--dry-run] [--apply] [--headed]
//     [--max-jobs=N] [--keyword="..."] [--location="..."]
//     [--pages-per-keyword=N] [--storage=<path>] [--verbose]
//
// Flags:
//   --dry-run      scrape-only (default behaviour; explicit for clarity)
//   --apply        actually open Easy Apply flow (not implemented fully; aborts
//                  modal and records status=dry_run unless v6 ships the FSM)
//   --headed       run with a visible browser (useful first-time for login)
//   --max-jobs     cap total scraped jobs across all keywords/locations
//   --keyword      override keyword list with a single keyword
//   --location     override location list with a single location
//   --storage      path to a storageState JSON for session reuse; defaults to
//                  ~/.cache/verbose-octo-carnival/linkedin_state.json
//   --verbose      log every skipped job, not just applied/error

import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';

import {
  env, profile, KEYWORDS, LOCATIONS, LIMITS,
  titleExcluded, extractSkills, extractEmail, searchUrl,
} from './lib/config.mjs';
import { launchStealthContext, persistStorageState } from './lib/stealth.mjs';
import { humanWait, humanScrollUntil, humanType, postApplyWait, sessionBreak } from './lib/human.mjs';
import { LOGIN, SEARCH, JOB_DETAIL, APPLY, firstVisible } from './lib/selectors.mjs';
import { RunOutput } from './lib/output.mjs';

// ── CLI parsing ─────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const out = { flags: new Set(), kv: {} };
  for (const a of argv.slice(2)) {
    if (a.startsWith('--')) {
      const eq = a.indexOf('=');
      if (eq > 0) out.kv[a.slice(2, eq)] = a.slice(eq + 1);
      else out.flags.add(a.slice(2));
    }
  }
  return out;
}

const args = parseArgs(process.argv);
const CFG = {
  dryRun: !args.flags.has('apply'),
  headed: args.flags.has('headed'),
  verbose: args.flags.has('verbose'),
  maxJobs: Number(args.kv['max-jobs']) || Infinity,
  keywords: args.kv.keyword ? [args.kv.keyword] : KEYWORDS,
  locations: args.kv.location !== undefined ? [args.kv.location] : LOCATIONS,
  pagesPerKeyword: Number(args.kv['pages-per-keyword']) || LIMITS.pagesPerKeyword,
  storage:
    args.kv.storage ||
    path.join(os.homedir(), '.cache', 'verbose-octo-carnival', 'linkedin_state.json'),
};

// ── Core flow ───────────────────────────────────────────────────────────────
async function loginIfNeeded(page, out) {
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });
  const url = page.url();
  if (url.includes('/feed') || url.includes('/mynetwork')) {
    out.info('Session restored from storageState — skipping login');
    return true;
  }

  if (!env.LINKEDIN_USERNAME || !env.LINKEDIN_PASSWORD) {
    out.error('No saved session and LINKIN_USERNAME / LINKIN_PASSWORD not set');
    return false;
  }

  out.info('Logging in…');
  await page.goto(LOGIN.url, { waitUntil: 'domcontentloaded' });
  await humanWait(1.5, 3);

  const emailEl = await firstVisible(page, LOGIN.emailCandidates, { timeout: 8000 });
  if (!emailEl) {
    await page.screenshot({ path: path.join(out.dir, 'login_page_error.png') });
    out.error('Could not find email field on /login');
    return false;
  }
  await humanType(emailEl, env.LINKEDIN_USERNAME);

  const pwdEl = await firstVisible(page, LOGIN.passwordCandidates, { timeout: 5000 });
  if (!pwdEl) {
    out.error('Could not find password field');
    return false;
  }
  await humanType(pwdEl, env.LINKEDIN_PASSWORD);

  const submitEl = await firstVisible(page, LOGIN.submitCandidates, { timeout: 5000 });
  if (!submitEl) {
    out.error('Could not find submit button');
    return false;
  }
  await submitEl.click();

  // Wait for nav; accept feed, checkpoint (2FA), or jobs.
  try {
    await page.waitForURL(
      (u) => LOGIN.feedCheckUrlFragments.some((f) => u.toString().includes(f)),
      { timeout: 20000 },
    );
  } catch {
    await page.screenshot({ path: path.join(out.dir, 'login_timeout.png') });
    out.error(`Login did not redirect to feed; landed at ${page.url()}`);
    return false;
  }
  if (page.url().includes('/checkpoint')) {
    out.warn('Hit checkpoint (CAPTCHA / 2FA). Complete it manually in --headed mode.');
    return false;
  }
  out.info('Login OK');
  return true;
}

async function collectJobCardsOnPage(page) {
  // Scroll the results list until no more new cards appear (or cap hit).
  let prev = 0;
  await humanScrollUntil(page, async () => {
    const count = await page.locator(SEARCH.jobCard).count();
    const done = count === prev && count > 0;
    prev = count;
    return done;
  }, { maxScrolls: 10 });
  return page.locator(SEARCH.jobCard);
}

async function readJobMeta(card) {
  const jobId = await card.getAttribute(SEARCH.jobCardJobIdAttr);
  const textOrEmpty = async (loc) => {
    try { return (await loc.first().innerText()).trim(); }
    catch { return ''; }
  };
  const title = await textOrEmpty(card.locator(SEARCH.jobCardTitle));
  const company = await textOrEmpty(card.locator(SEARCH.jobCardCompany));
  const location = await textOrEmpty(card.locator(SEARCH.jobCardLocation));
  let url = '';
  try {
    const href = await card.locator(SEARCH.jobCardTitle).first().getAttribute('href');
    if (href) url = new URL(href, 'https://www.linkedin.com').toString();
  } catch { /* noop */ }
  return { jobId, title, company, location, url };
}

async function readDescription(page) {
  for (const sel of JOB_DETAIL.descriptionCandidates) {
    const loc = page.locator(sel).first();
    try {
      if ((await loc.count()) > 0) return (await loc.innerText()).trim();
    } catch { /* keep trying */ }
  }
  return '';
}

/** Stub for the Easy Apply modal FSM. v5 ships the scraper half of the
 *  refactor; the full modal FSM port is tracked for v6. If --apply is passed
 *  we open the dialog, snapshot it, then dismiss, so the behaviour is
 *  equivalent to v4's --dry-run. */
async function tryEasyApply(page, out, jobId) {
  const btn = page.locator(APPLY.easyBtn).first();
  if ((await btn.count()) === 0) return { status: 'skipped', note: 'no_easy_apply_button' };
  await btn.click();
  await humanWait(1, 2);
  await page.screenshot({ path: path.join(out.dir, `apply_${jobId}.png`) });
  // Dismiss without submitting — the modal FSM is not yet ported.
  const dismiss = page.locator(APPLY.dismissBtn).first();
  if ((await dismiss.count()) > 0) {
    await dismiss.click();
    await humanWait(0.5, 1);
    const discard = page.locator(APPLY.discardConfirm).first();
    if ((await discard.count()) > 0) await discard.click();
  }
  return { status: 'dry_run', note: 'modal_fsm_not_ported' };
}

async function scrape() {
  const out = new RunOutput({ rootDir: process.cwd(), runLabel: 'linkedin_v5' });
  out.info(`v5 scraper starting — runId=${out.runId}`);
  out.info(`  dryRun=${CFG.dryRun}  headed=${CFG.headed}  maxJobs=${CFG.maxJobs}`);
  out.info(`  keywords=${CFG.keywords.length}  locations=${CFG.locations.length}  pages=${CFG.pagesPerKeyword}`);
  out.info(`  profile=${profile.fullName} (${profile.homeCity})`);

  let browser, context;
  try {
    const launched = await launchStealthContext(chromium, {
      headless: !CFG.headed,
      storageState: CFG.storage,
    });
    browser = launched.browser;
    context = launched.context;
    out.info(`  identity=${context._v5.ident.platform} ${context._v5.viewport.width}x${context._v5.viewport.height} tz=${context._v5.timezoneId}`);

    const page = await context.newPage();

    if (!(await loginIfNeeded(page, out))) return;
    await persistStorageState(context, CFG.storage);

    let appliesThisSession = 0;

    outer: for (const location of CFG.locations) {
      for (const keyword of CFG.keywords) {
        if (out.summary().total >= CFG.maxJobs) break outer;
        out.info(`── keyword="${keyword}"  location="${location || '(any)'}"`);

        for (let pageIdx = 0; pageIdx < CFG.pagesPerKeyword; pageIdx++) {
          const start = pageIdx * LIMITS.jobsPerPage;
          const url = searchUrl(keyword, location, start);
          try {
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
          } catch (e) {
            out.warn(`  goto failed: ${e.message}`);
            continue;
          }
          await humanWait(2, 3.5);

          const cards = await collectJobCardsOnPage(page);
          const n = await cards.count();
          out.info(`  page ${pageIdx + 1}: ${n} cards`);

          for (let i = 0; i < n; i++) {
            if (out.summary().total >= CFG.maxJobs) break outer;

            let meta;
            try {
              meta = await readJobMeta(cards.nth(i));
            } catch {
              continue;
            }
            if (!meta.jobId || out.seen(meta.jobId)) continue;

            const exclude = titleExcluded(meta.title);
            if (exclude) {
              if (CFG.verbose) out.info(`  skip "${meta.title}" — title_excluded:${exclude}`);
              out.add({ ...rec(meta, keyword), status: 'skipped', note: `title_excluded:${exclude}` });
              continue;
            }

            // Click the card to reveal the right-hand detail pane.
            try {
              await cards.nth(i).scrollIntoViewIfNeeded();
              await cards.nth(i).click({ timeout: 5000 });
            } catch {
              // If click fails (stale DOM), skip but still record metadata.
              out.add({ ...rec(meta, keyword), status: 'error', note: 'card_click_failed' });
              continue;
            }
            await humanWait(1.2, 2.3);

            const desc = await readDescription(page);
            const skills = extractSkills(desc);
            const email = extractEmail(desc);
            const base = { ...rec(meta, keyword), skills_mentioned: skills, contact_email: email };

            if (!CFG.dryRun && appliesThisSession < LIMITS.maxAppliesPerSession) {
              const result = await tryEasyApply(page, out, meta.jobId);
              out.add({ ...base, status: result.status, note: result.note });
              if (result.status === 'applied' || result.status === 'dry_run') {
                appliesThisSession += 1;
                await postApplyWait();
                if (appliesThisSession % LIMITS.sessionBreakEvery === 0) {
                  out.info(`  session break after ${appliesThisSession} applies`);
                  await sessionBreak();
                }
              }
            } else {
              out.add({ ...base, status: 'scraped', note: '' });
            }
          }
        }
      }
    }

    await persistStorageState(context, CFG.storage);
  } catch (e) {
    out.error(`fatal: ${e.stack || e.message}`);
  } finally {
    try { await context?.close(); } catch {}
    try { await browser?.close(); } catch {}
    out.save();
    const s = out.summary();
    out.info(`Done. total=${s.total} by_status=${JSON.stringify(s.by)}`);
    out.close();
  }
}

/** Build a JobRecord skeleton from card metadata. */
function rec(meta, keyword) {
  return {
    job_id: meta.jobId,
    title: meta.title,
    company: meta.company,
    location: meta.location,
    keyword,
    url: meta.url,
    platform: 'LinkedIn',
    apply_type: 'easy_apply',
  };
}

// Only execute when invoked directly (not when imported for testing).
const invokedDirectly = import.meta.url === `file://${process.argv[1]}` ||
  process.argv[1]?.endsWith('linkedin_scraper.mjs');
if (invokedDirectly) {
  scrape().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}

export { scrape, parseArgs };
