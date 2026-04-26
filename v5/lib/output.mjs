// v5/lib/output.mjs — CSV/JSON output pipeline.
//
// Replaces the save_all() function from v4 (035_linkedin_easy_apply_pa.py:165).
// Responsibilities:
//   • Build a timestamped run directory under runs/linkedin_v5_<ts>/
//   • Stream records to jobs.jsonl as they're produced (crash-safe)
//   • Emit final jobs.json + jobs.csv + gmass_contacts.csv at save()
//   • Track a seen-job-id set to dedupe within a run
//
// CSV schema matches library/gsheets.py COLUMNS so the Google Sheets sync
// layer (if the user ports it later) can consume v5 output unchanged.

import fs from 'node:fs';
import path from 'node:path';

/**
 * @typedef {object} JobRecord
 * @property {string} job_id
 * @property {string} title
 * @property {string} company
 * @property {string} location
 * @property {string} keyword
 * @property {string} status              applied|skipped|error|dry_run|scraped
 * @property {string} [url]
 * @property {string} [apply_type]        easy_apply|external|unknown
 * @property {string} [platform]          default LinkedIn
 * @property {number|null} [days_since_posted]
 * @property {string} [skills_mentioned]
 * @property {string} [contact_email]
 * @property {string} [note]
 * @property {string} [timestamp]         ISO 8601; auto-filled
 */

const JOB_FIELDS = [
  'job_id', 'title', 'company', 'location', 'keyword', 'status', 'url',
  'apply_type', 'platform', 'days_since_posted', 'skills_mentioned',
  'contact_email', 'note', 'timestamp',
];

const GMASS_FIELDS = [
  'Email', 'First Name', 'Last Name', 'Company', 'Title', 'Job URL',
  'Location', 'Skills',
];

function csvEscape(val) {
  if (val === null || val === undefined) return '';
  const s = String(val);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function writeCsv(filePath, fields, rows) {
  const lines = [fields.join(',')];
  for (const row of rows) lines.push(fields.map((f) => csvEscape(row[f])).join(','));
  fs.writeFileSync(filePath, lines.join('\n') + '\n', 'utf-8');
}

export class RunOutput {
  /**
   * @param {object} opts
   * @param {string}  [opts.rootDir]   parent of runs/ (default: cwd)
   * @param {string}  [opts.runLabel]  folder prefix (default: linkedin_v5)
   */
  constructor(opts = {}) {
    const rootDir = opts.rootDir || process.cwd();
    const runLabel = opts.runLabel || 'linkedin_v5';
    const ts = new Date().toISOString()
      .replace(/[:T]/g, '-')
      .replace(/\..+$/, '')      // drop millis + Z
      .replace(/-(\d{2})$/, '-$1'); // keep HH-MM-SS
    this.runId = ts;
    this.dir = path.join(rootDir, 'runs', `${runLabel}_${ts}`);
    fs.mkdirSync(this.dir, { recursive: true });

    this.jsonPath = path.join(this.dir, 'jobs.json');
    this.jsonlPath = path.join(this.dir, 'jobs.jsonl');
    this.csvPath = path.join(this.dir, 'jobs.csv');
    this.gmassPath = path.join(this.dir, 'gmass_contacts.csv');
    this.logPath = path.join(this.dir, 'run.log');
    this.storagePath = path.join(this.dir, 'storage_state.json');

    this._records = [];
    this._seenIds = new Set();
    this._jsonlStream = fs.createWriteStream(this.jsonlPath, { flags: 'a' });
    this._logStream = fs.createWriteStream(this.logPath, { flags: 'a' });
  }

  /** Human-readable log line — also echoed to stdout so launchd captures it. */
  log(level, msg) {
    const ts = new Date().toISOString().slice(11, 19);
    const line = `${ts} | ${level.padEnd(7)} | ${msg}`;
    this._logStream.write(line + '\n');
    process.stdout.write(line + '\n');
  }

  info(msg) { this.log('INFO', msg); }
  warn(msg) { this.log('WARN', msg); }
  error(msg) { this.log('ERROR', msg); }

  /** Have we already recorded this job_id this run? */
  seen(jobId) {
    return this._seenIds.has(jobId);
  }

  /** Append a record. Silently dedupes on job_id. Returns false if dup. */
  add(rec) {
    if (!rec.job_id) return false;
    if (this._seenIds.has(rec.job_id)) return false;
    this._seenIds.add(rec.job_id);

    const normalized = {
      platform: 'LinkedIn',
      apply_type: 'easy_apply',
      days_since_posted: null,
      skills_mentioned: '',
      contact_email: '',
      note: '',
      url: '',
      timestamp: new Date().toISOString(),
      ...rec,
    };
    this._records.push(normalized);
    this._jsonlStream.write(JSON.stringify(normalized) + '\n');
    return true;
  }

  /** Counts grouped by status, handy for the end-of-run summary. */
  summary() {
    const by = {};
    for (const r of this._records) by[r.status] = (by[r.status] || 0) + 1;
    return { total: this._records.length, by };
  }

  /** Returns a snapshot of records (for downstream sync, tests, etc). */
  records() {
    return [...this._records];
  }

  /** Flush final jobs.json, jobs.csv, gmass_contacts.csv. */
  save() {
    fs.writeFileSync(
      this.jsonPath,
      JSON.stringify(this._records, null, 2),
      'utf-8',
    );
    writeCsv(this.csvPath, JOB_FIELDS, this._records);

    const gmassRows = this._records
      .filter((r) => r.contact_email)
      .map((r) => ({
        Email: r.contact_email,
        'First Name': '',
        'Last Name': '',
        Company: r.company,
        Title: r.title,
        'Job URL': r.url,
        Location: r.location,
        Skills: r.skills_mentioned,
      }));
    if (gmassRows.length) {
      writeCsv(this.gmassPath, GMASS_FIELDS, gmassRows);
      this.info(`GMass contacts: ${gmassRows.length} emails → ${this.gmassPath}`);
    } else {
      this.info('GMass contacts: no recruiter emails found this run');
    }
    this.info(`Saved ${this._records.length} jobs → ${this.dir}`);
  }

  /** Close streams — call from finally{}. */
  close() {
    try { this._jsonlStream.end(); } catch {}
    try { this._logStream.end(); } catch {}
  }
}
