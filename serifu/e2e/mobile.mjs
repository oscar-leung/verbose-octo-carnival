// Phone-viewport E2E: the room is a three-tab app on small screens.
import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';

const BASE = process.env.BASE ?? 'http://localhost:4123';
const SHOTS = new URL('./shots', import.meta.url).pathname;
mkdirSync(SHOTS, { recursive: true });
const results = [];
const check = (label, ok) => {
  results.push([label, ok]);
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}`);
  if (!ok) process.exitCode = 1;
};

const browser = await chromium.launch({
  ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}),
  headless: true,
  args: ['--no-sandbox'],
});
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });

const noHScroll = () =>
  page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);

// ---- landing ----
await page.goto(BASE);
await page.waitForSelector('.landing-card');
check('landing: no horizontal scroll at 390px', await noHScroll());

// ---- room: stage tab is the default ----
await page.fill('input[placeholder*="名前"]', 'Sumaho');
await page.click('button:has-text("Create a room")');
await page.waitForSelector('.mobile-nav');
check('room: bottom tab bar renders', true);
check('stage tab: video visible', await page.isVisible('.video-wrap'));
check('stage tab: script hidden', !(await page.isVisible('.script-panel')));
await page.screenshot({ path: `${SHOTS}/m1-stage.png` });

// ---- script tab: load a scene, lines appear ----
await page.click('.mnav-btn:has-text("台本")');
await page.waitForSelector('.scene-list');
await page.click('.scene-btn >> nth=0');
await page.waitForSelector('.line');
check('script tab: scene loads and lines render', true);
check('script tab: video hidden', !(await page.isVisible('.video-wrap')));
check('script tab: no horizontal scroll', await noHScroll());
await page.screenshot({ path: `${SHOTS}/m2-script.png` });

// ---- more tab: tools grid + settings ----
await page.click('.mnav-btn:has-text("その他")');
await page.waitForSelector('.more-actions');
check(
  'more tab: tool buttons + settings visible',
  (await page.isVisible('.more-actions button:has-text("単語帳")')) &&
    (await page.isVisible('.settings-row'))
);
await page.screenshot({ path: `${SHOTS}/m3-more.png` });

// ---- back to stage ----
await page.click('.mnav-btn:has-text("ステージ")');
check('stage tab again: video back', await page.isVisible('.video-wrap'));
check('touch targets: nav buttons ≥ 44px tall', await page.evaluate(() => {
  const b = document.querySelector('.mnav-btn');
  return b && b.getBoundingClientRect().height >= 44;
}));

console.log('---');
for (const [label, ok] of results) if (!ok) console.log('FAILED:', label);
console.log(`${results.filter(([, ok]) => ok).length}/${results.length} mobile checks passed`);
await browser.close();
process.exit(process.exitCode ?? 0);
