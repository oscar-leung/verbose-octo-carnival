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
check(
  'landing: 3 solo chips + もっと見る keep the first viewport short',
  (await page.$$eval('.solo-links a.chip', (els) => els.length)) === 3 &&
    (await page.isVisible('.solo-links button:has-text("もっと見る")'))
);

// ---- room: stage tab is the default ----
await page.fill('input[placeholder*="名前"]', 'Sumaho');
await page.click('button:has-text("Create a room")');
await page.waitForSelector('.mobile-nav');
check('room: bottom tab bar renders', true);
check('stage tab: video visible', await page.isVisible('.video-wrap'));
check('stage tab: script hidden', !(await page.isVisible('.script-panel')));
await page.screenshot({ path: `${SHOTS}/m1-stage.png` });

// ---- empty stage: video-less escape hatch straight to the script ----
check('stage tab: 台本へ escape link visible', await page.isVisible('.placeholder-script-link'));
await page.click('.placeholder-script-link');
await page.waitForSelector('.script-panel');
check('台本へ link switches to the script tab', await page.isVisible('.script-panel'));

// ---- script tab: load a scene, lines appear ----
await page.click('.mnav-btn:has-text("台本")');
await page.waitForSelector('.scene-list');
await page.click('.scene-btn >> nth=0');
await page.waitForSelector('.line');
check('script tab: scene loads and lines render', true);
check('script tab: video hidden', !(await page.isVisible('.video-wrap')));
check('script tab: no horizontal scroll', await noHScroll());
await page.screenshot({ path: `${SHOTS}/m2-script.png` });

// ---- translation reveal: blurred until pressed (no hover on phones) ----
const translation = page.locator('.line-translation.hover-reveal').first();
await translation.scrollIntoViewIfNeeded();
check(
  'script tab: translation blurred (タップ mode)',
  (await translation.evaluate((el) => getComputedStyle(el).filter)).includes('blur')
);
const tBox = await translation.boundingBox();
await page.mouse.move(tBox.x + 10, tBox.y + tBox.height / 2);
await page.mouse.down();
const pressRevealed = await page
  .waitForFunction(
    () => {
      const el = document.querySelector('.line-translation.hover-reveal');
      return el && getComputedStyle(el).filter === 'none';
    },
    { timeout: 3000 }
  )
  .then(() => true)
  .catch(() => false);
await page.mouse.up();
check('script tab: pressing a translation reveals it', pressRevealed);

// ---- more tab: tools grid + settings ----
await page.click('.mnav-btn:has-text("その他")');
await page.waitForSelector('.more-actions');
check(
  'more tab: tool buttons + settings visible',
  (await page.isVisible('.more-actions button:has-text("単語帳")')) &&
    (await page.isVisible('.settings-row'))
);
check(
  'more tab: tool buttons carry EN sublabels',
  await page.isVisible('.more-actions button small:has-text("wordbook")')
);
check(
  'more tab: auto-pause + 判定 settings live here',
  (await page.isVisible('.settings-row .mobile-room-setting:has-text("セリフで自動停止")')) &&
    (await page.isVisible('.settings-row .mobile-room-setting select'))
);
await page.screenshot({ path: `${SHOTS}/m3-more.png` });

// ---- back to stage ----
await page.click('.mnav-btn:has-text("ステージ")');
check('stage tab again: video back', await page.isVisible('.video-wrap'));
check(
  'stage tab: only claim chips — rehearsal settings moved to その他',
  (await page.isVisible('.character-bar .char-pill')) &&
    !(await page.isVisible('.character-bar .rehearsal-toggle')) &&
    !(await page.isVisible('.character-bar .pass-toggle'))
);
check('touch targets: nav buttons ≥ 44px tall', await page.evaluate(() => {
  const b = document.querySelector('.mnav-btn');
  return b && b.getBoundingClientRect().height >= 44;
}));

// ---- solo practice: primary action stays under the thumb ----
await page.goto(`${BASE}/#/p/meteor-promise`);
await page.waitForSelector('.solo-nav');
check('solo: no horizontal scroll', await noHScroll());
check(
  'solo: header shows the scene name, not the series prefix',
  !(((await page.textContent('.solo-title')) ?? '').includes('葬送のフリーレン'))
);
check('solo: next/skip nav sticky within the first viewport', await page.evaluate(() => {
  const nav = document.querySelector('.solo-nav');
  if (!nav) return false;
  const r = nav.getBoundingClientRect();
  return getComputedStyle(nav).position === 'sticky' && r.bottom <= window.innerHeight + 1;
}));
check('solo: hide levels render as one four-column row', await page.evaluate(() => {
  const chips = [...document.querySelectorAll('.hide-levels .chip')];
  return (
    chips.length === 4 &&
    new Set(chips.map((c) => Math.round(c.getBoundingClientRect().top))).size === 1
  );
}));
await page.screenshot({ path: `${SHOTS}/m4-solo.png` });

// ---- 文法さくいん: reachable from the その他 tab on phones ----
await page.goto(`${BASE}/#/r/gidx${Date.now().toString(36)}`);
await page.waitForSelector('.mobile-nav');
await page.click('.mnav-btn:has-text("その他")');
await page.waitForSelector('.more-actions');
check(
  'more tab: 文法 button visible with EN sublabel',
  (await page.isVisible('.more-actions button:has-text("文法")')) &&
    (await page.isVisible('.more-actions button small:has-text("grammar")'))
);
await page.click('.more-actions button:has-text("文法")');
await page.waitForSelector('.modal.grammar-index');
check('文法 opens the grammar index modal', await page.isVisible('.gi-search'));
check('grammar rows are ≥42px touch targets', await page.evaluate(() => {
  const r = document.querySelector('.gi-row');
  return r && r.getBoundingClientRect().height >= 42;
}));
await page.screenshot({ path: `${SHOTS}/m5-grammar-index.png` });
await page.click('.modal.grammar-index .modal-header button');
await page.waitForSelector('.modal.grammar-index', { state: 'detached', timeout: 3000 });
check('grammar index closes', true);

console.log('---');
for (const [label, ok] of results) if (!ok) console.log('FAILED:', label);
console.log(`${results.filter(([, ok]) => ok).length}/${results.length} mobile checks passed`);
await browser.close();
process.exit(process.exitCode ?? 0);
