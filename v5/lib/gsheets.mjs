// v5/lib/gsheets.mjs — Node port of library/gsheets.py.
//
// Appends new job rows to the "Applications" tab of a Google Sheet, matching
// the COLUMNS schema used by every other script in the suite. Dedupe key is
// "platform|job_id" — same as the Python version. Uses the `googleapis`
// package with a service-account JSON. If env vars or the package are
// missing, `syncJobs()` returns a soft-skip result rather than throwing,
// so the scraper still completes successfully without sheets configured.
//
// Required env (loaded via lib/config.mjs):
//   GOOGLE_SERVICE_ACCOUNT_JSON  — absolute path to service-account JSON key
//   GOOGLE_SHEET_ID              — the sheet ID (from its URL)

import fs from 'node:fs';
import { env } from './config.mjs';

const COLUMNS = [
  'date_applied', 'platform', 'job_id', 'title', 'company', 'location',
  'remote_type', 'url', 'employment_type', 'salary_min', 'salary_max',
  'salary_unit', 'skills_mentioned', 'apply_type', 'status',
  'days_since_posted', 'notes',
];

const SHEET_NAME = 'Applications';

function jobToRow(job, platform) {
  const location = job.location_raw || job.location || job.city || '';
  const ts = job.timestamp || new Date().toISOString();
  return [
    ts.slice(0, 10),                            // date_applied (YYYY-MM-DD)
    platform,
    String(job.job_id || ''),
    job.title || '',
    job.company || '',
    location,
    job.remote_type || '',
    job.url || '',
    job.employment_type || '',
    job.salary_min || '',
    job.salary_max || '',
    job.salary_unit || '',
    job.skills_mentioned || '',
    job.apply_type || '',
    job.status || '',
    job.days_since_posted ?? '',
    job.note || job.notes || '',
  ];
}

/** Lazy-load googleapis. Returns null if not installed. */
async function loadSheetsClient(serviceAccountJsonPath) {
  let google;
  try {
    ({ google } = await import('googleapis'));
  } catch {
    return null;
  }
  const auth = new google.auth.GoogleAuth({
    keyFile: serviceAccountJsonPath,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
  return google.sheets({ version: 'v4', auth });
}

/** Read existing rows and return Set of "platform|job_id" already synced. */
async function existingIds(sheets, sheetId) {
  try {
    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: sheetId,
      range: `${SHEET_NAME}!A:Q`,
    });
    const rows = res.data.values || [];
    if (rows.length === 0) return new Set();
    const header = rows[0];
    const platformIdx = header.indexOf('platform');
    const jobIdIdx = header.indexOf('job_id');
    if (platformIdx < 0 || jobIdIdx < 0) return new Set();
    return new Set(
      rows.slice(1)
        .filter((r) => r[jobIdIdx])
        .map((r) => `${r[platformIdx] || ''}|${r[jobIdIdx]}`),
    );
  } catch {
    return new Set();
  }
}

/** Ensure the Applications tab exists with a header row. */
async function ensureSheet(sheets, sheetId, log) {
  try {
    const meta = await sheets.spreadsheets.get({ spreadsheetId: sheetId });
    const exists = (meta.data.sheets || []).some((s) => s.properties?.title === SHEET_NAME);
    if (exists) return;
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: sheetId,
      requestBody: { requests: [{ addSheet: { properties: { title: SHEET_NAME } } }] },
    });
    await sheets.spreadsheets.values.update({
      spreadsheetId: sheetId,
      range: `${SHEET_NAME}!A1`,
      valueInputOption: 'USER_ENTERED',
      requestBody: { values: [COLUMNS] },
    });
    log?.info?.(`gsheets: created '${SHEET_NAME}' worksheet with headers`);
  } catch (e) {
    throw new Error(`ensureSheet failed: ${e.message}`);
  }
}

/**
 * Append new jobs to the configured Google Sheet.
 *
 * @param {Array<object>} jobs       records from RunOutput.records()
 * @param {string} platform           "LinkedIn" | "Handshake" | "Indeed" | ...
 * @param {object} [opts]
 * @param {boolean} [opts.appliedOnly]  default false — only sync status=applied
 * @param {object}  [opts.log]          logger with .info/.warn
 * @returns {Promise<{appended: number, skipped: string}>}
 */
export async function syncJobs(jobs, platform, opts = {}) {
  const log = opts.log;
  if (!jobs || jobs.length === 0) return { appended: 0, skipped: 'no_jobs' };
  if (!env.GOOGLE_SERVICE_ACCOUNT_JSON || !env.GOOGLE_SHEET_ID) {
    log?.info?.('gsheets: GOOGLE_SERVICE_ACCOUNT_JSON / GOOGLE_SHEET_ID not set — skipping sync');
    return { appended: 0, skipped: 'no_credentials' };
  }
  if (!fs.existsSync(env.GOOGLE_SERVICE_ACCOUNT_JSON)) {
    log?.warn?.(`gsheets: service-account file not found at ${env.GOOGLE_SERVICE_ACCOUNT_JSON}`);
    return { appended: 0, skipped: 'no_credentials_file' };
  }

  const sheets = await loadSheetsClient(env.GOOGLE_SERVICE_ACCOUNT_JSON);
  if (!sheets) {
    log?.warn?.('gsheets: googleapis package not installed — run `npm install googleapis` to enable sync');
    return { appended: 0, skipped: 'package_missing' };
  }

  await ensureSheet(sheets, env.GOOGLE_SHEET_ID, log);
  const existing = await existingIds(sheets, env.GOOGLE_SHEET_ID);

  const rows = [];
  for (const job of jobs) {
    if (opts.appliedOnly && job.status !== 'applied') continue;
    const uid = `${platform}|${job.job_id || ''}`;
    if (existing.has(uid)) continue;
    rows.push(jobToRow(job, platform));
  }
  if (rows.length === 0) return { appended: 0, skipped: 'all_dupes' };

  await sheets.spreadsheets.values.append({
    spreadsheetId: env.GOOGLE_SHEET_ID,
    range: `${SHEET_NAME}!A:Q`,
    valueInputOption: 'USER_ENTERED',
    requestBody: { values: rows },
  });
  return { appended: rows.length, skipped: '' };
}

export { COLUMNS, jobToRow };
