// v5/lib/config.mjs — env loader, keyword/filter config, session caps.
//
// Ports the hardcoded config block from 035_linkedin_easy_apply_pa.py
// (KEYWORDS, TITLE_EXCLUDE, LOCATIONS, pagination, caps) into one place
// so the main scraper stays declarative.

import path from 'node:path';
import fs from 'node:fs';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..', '..');

// ── .env loader (no dotenv dep required) ─────────────────────────────────────
function loadDotenv(envPath) {
  if (!fs.existsSync(envPath)) return;
  const raw = fs.readFileSync(envPath, 'utf-8');
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq < 0) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = val;
  }
}
loadDotenv(path.join(REPO_ROOT, '.env'));

export const env = {
  LINKEDIN_USERNAME: process.env.LINKIN_USERNAME || process.env.LINKEDIN_USERNAME || '',
  LINKEDIN_PASSWORD: process.env.LINKIN_PASSWORD || process.env.LINKEDIN_PASSWORD || '',
  GOOGLE_SERVICE_ACCOUNT_JSON: process.env.GOOGLE_SERVICE_ACCOUNT_JSON || '',
  GOOGLE_SHEET_ID: process.env.GOOGLE_SHEET_ID || '',
};

// ── Profile (identity the scraper operates as) ──────────────────────────────
export const profile = {
  fullName: 'Oscar Leung',
  linkedinUrl: 'https://www.linkedin.com/in/oscar-leung/',
  homeCity: 'Santa Clara',
};

// ── Keywords, title blocklist, locations — ported from v4 (lines 73–107) ────
export const KEYWORDS = [
  'QA Automation Engineer',
  'SDET',
  'Software Engineer in Test',
  'Quality Engineer',
  'Test Engineer',
  'Automation Engineer',
  'Python Developer',
  'Python Engineer',
  'Backend Engineer',
  'Java Developer',
  'Java Engineer',
  'Software Engineer',
  'Web Developer',
  'Full Stack Engineer',
];

// Title tokens that disqualify a posting (case-insensitive substring match).
export const TITLE_EXCLUDE = [
  'senior', ' sr ', 'sr.', 'staff', 'principal', 'lead', 'manager',
  'director', 'vp', 'intern', 'sales', 'hardware', 'embedded', 'devops',
  'founding', 'product', 'robotics', 'campus', 'customer', 'digital',
  'firmware', 'field',
];

// Empty string = LinkedIn default (all locations / remote-friendly).
export const LOCATIONS = ['', 'Sacramento, CA', 'Davis, CA'];

// ── Pagination & caps ───────────────────────────────────────────────────────
export const LIMITS = {
  pagesPerKeyword: 2,
  jobsPerPage: 25,
  maxAppliesPerSession: 8,
  sessionBreakEvery: 4,
  sessionBreakSecs: [60, 120],
  modalMaxSteps: 20,
  waitSec: 10,
};

// ── Skills extracted from descriptions ──────────────────────────────────────
export const SKILLS = [
  'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
  'selenium', 'playwright', 'cypress', 'appium', 'testng', 'junit',
  'node', 'sql', 'postgresql', 'mongodb', 'aws', 'azure', 'gcp',
  'docker', 'kubernetes', 'git', 'ci/cd', 'jenkins', 'github actions',
  'rest', 'graphql', 'django', 'flask', 'fastapi', 'spring',
  'html', 'css', 'tailwind', 'agile', 'scrum', 'jira',
  'linux', 'bash', 'terraform', 'qa', 'automation', 'testing',
  'machine learning', 'pytorch', 'tensorflow',
];

export const EMAIL_BLOCKLIST = new Set([
  'linkedin.com', 'example.com', 'sentry.io', 'w3.org', 'schema.org',
]);

export function titleExcluded(title) {
  const low = (title || '').toLowerCase();
  return TITLE_EXCLUDE.find((tok) => low.includes(tok)) || null;
}

export function extractSkills(text) {
  if (!text) return '';
  const low = text.toLowerCase();
  return SKILLS.filter((s) => low.includes(s)).join(', ');
}

const EMAIL_RE = /[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/gi;
export function extractEmail(text) {
  if (!text) return '';
  for (const match of text.matchAll(EMAIL_RE)) {
    const addr = match[0].toLowerCase();
    const domain = addr.split('@').pop();
    if (!EMAIL_BLOCKLIST.has(domain)) return addr;
  }
  return '';
}

// ── Search URL builder (matches v4's search_url()) ──────────────────────────
// f_LF=f_AL forces "Easy Apply only" filter.
export function searchUrl(keyword, location, start = 0) {
  const kw = encodeURIComponent(keyword);
  const loc = location ? `&location=${encodeURIComponent(location)}` : '';
  return `https://www.linkedin.com/jobs/search/?keywords=${kw}&f_LF=f_AL${loc}&start=${start}`;
}

export { REPO_ROOT };
