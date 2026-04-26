// tests/v5_smoke.test.mjs — fast unit tests for v5 lib modules.
//
// Run with: node --test tests/v5_smoke.test.mjs
// Verifies: config filters, output pipeline (CSV escaping + dedup), and
// gsheets jobToRow mapping. All deterministic — no Playwright, no network.

import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import {
  KEYWORDS, TITLE_EXCLUDE, LOCATIONS, titleExcluded,
  extractSkills, extractEmail, searchUrl,
} from '../v5/lib/config.mjs';
import { RunOutput } from '../v5/lib/output.mjs';
import { jobToRow, COLUMNS } from '../v5/lib/gsheets.mjs';

test('config: KEYWORDS / TITLE_EXCLUDE / LOCATIONS shape', () => {
  assert.ok(KEYWORDS.length >= 10, 'should ship a healthy keyword list');
  assert.ok(TITLE_EXCLUDE.includes('senior'), 'must filter senior roles');
  assert.ok(LOCATIONS[0] === '', 'first location is "any" (empty string)');
});

test('config: titleExcluded matches v4 semantics', () => {
  assert.equal(titleExcluded('Senior Software Engineer'), 'senior');
  assert.equal(titleExcluded('Engineering Manager'), 'manager');
  assert.equal(titleExcluded('QA Engineer'), null);
  assert.equal(titleExcluded('Software Engineer in Test'), null);
  assert.equal(titleExcluded(''), null);
  assert.equal(titleExcluded(undefined), null);
});

test('config: extractSkills finds matches case-insensitively', () => {
  const desc = 'We use Python, Docker, and Selenium for our QA pipeline.';
  const skills = extractSkills(desc);
  assert.ok(skills.includes('python'));
  assert.ok(skills.includes('docker'));
  assert.ok(skills.includes('selenium'));
  assert.equal(extractSkills(''), '');
});

test('config: extractEmail filters blocklisted domains', () => {
  assert.equal(
    extractEmail('Email recruiter@acme.io for questions'),
    'recruiter@acme.io',
  );
  assert.equal(
    extractEmail('Auto: noreply@linkedin.com — do not reply'),
    '',
    'linkedin.com is blocklisted',
  );
  assert.equal(
    extractEmail('contact noreply@linkedin.com or hr@startup.co'),
    'hr@startup.co',
    'should skip blocklisted and return next valid',
  );
});

test('config: searchUrl encodes parameters and adds Easy Apply filter', () => {
  const url = searchUrl('SDET', 'San Francisco, CA', 25);
  assert.ok(url.includes('keywords=SDET'));
  assert.ok(url.includes('f_LF=f_AL'), 'must include Easy Apply filter');
  assert.ok(url.includes('location=San%20Francisco%2C%20CA'));
  assert.ok(url.includes('start=25'));
});

test('output: dedupes by job_id', () => {
  const out = new RunOutput({ rootDir: fs.mkdtempSync(path.join(os.tmpdir(), 'v5-')) });
  try {
    assert.equal(
      out.add({ job_id: 'a', title: 'T', company: 'C', location: 'L', keyword: 'k', status: 'scraped' }),
      true,
    );
    assert.equal(
      out.add({ job_id: 'a', title: 'dup', company: 'x', location: 'x', keyword: 'k', status: 'scraped' }),
      false,
    );
    assert.equal(out.summary().total, 1);
    assert.equal(out.seen('a'), true);
    assert.equal(out.seen('b'), false);
  } finally {
    out.close();
  }
});

test('output: CSV escapes quotes, commas, newlines', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'v5-'));
  const out = new RunOutput({ rootDir: tmp });
  try {
    out.add({
      job_id: '1',
      title: 'QA, with "quotes"\nand newline',
      company: 'Co',
      location: 'NY',
      keyword: 'k',
      status: 'scraped',
    });
    out.save();
    const csv = fs.readFileSync(out.csvPath, 'utf-8');
    // The escaped cell should contain doubled quotes and be wrapped in quotes.
    assert.ok(csv.includes('"QA, with ""quotes""\nand newline"'));
  } finally {
    out.close();
  }
});

test('output: gmass_contacts.csv only includes rows with emails', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'v5-'));
  const out = new RunOutput({ rootDir: tmp });
  try {
    out.add({ job_id: '1', title: 'A', company: 'Co', location: 'X', keyword: 'k', status: 'scraped', contact_email: 'r@a.io' });
    out.add({ job_id: '2', title: 'B', company: 'Co', location: 'X', keyword: 'k', status: 'scraped' });
    out.save();
    const gmass = fs.readFileSync(out.gmassPath, 'utf-8').trim().split('\n');
    assert.equal(gmass.length, 2, 'header + 1 data row');
    assert.ok(gmass[1].startsWith('r@a.io,'));
  } finally {
    out.close();
  }
});

test('gsheets: jobToRow produces COLUMNS-shaped array', () => {
  const job = {
    job_id: '42',
    title: 'SDET',
    company: 'Acme',
    location: 'Remote',
    url: 'https://x',
    apply_type: 'easy_apply',
    status: 'applied',
    skills_mentioned: 'python, docker',
    timestamp: '2026-04-23T12:00:00Z',
    note: 'submitted_step_5',
  };
  const row = jobToRow(job, 'LinkedIn');
  assert.equal(row.length, COLUMNS.length, 'row width matches COLUMNS');
  assert.equal(row[0], '2026-04-23', 'date_applied is YYYY-MM-DD');
  assert.equal(row[1], 'LinkedIn');
  assert.equal(row[2], '42');
  assert.equal(row[3], 'SDET');
  assert.equal(row[14], 'applied');
  assert.equal(row[16], 'submitted_step_5');
});
