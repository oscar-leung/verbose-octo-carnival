// Store-screenshot capture for Serifu — drives the real app at :4600.
// Seeds all state via the UI (paste-import of an original, anime-agnostic
// script; controllable fake SpeechRecognition; fake media device flags).
import { chromium } from 'playwright-core';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';

const BASE = process.env.BASE ?? 'http://localhost:4600';
const OUT = new URL('..', import.meta.url).pathname.replace(/\/$/, '');
const HERE = new URL('.', import.meta.url).pathname;
const TMP = process.env.TMPDIR ?? '/tmp';
mkdirSync(OUT, { recursive: true });

const scriptJson = readFileSync(`${HERE}/script.json`, 'utf8');
const log = (m) => console.log(`[capture] ${m}`);

const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  headless: true,
  args: [
    '--no-sandbox',
    '--autoplay-policy=no-user-gesture-required',
    '--use-fake-ui-for-media-stream',
    '--use-fake-device-for-media-stream',
    '--font-render-hinting=none',
  ],
});

// 412x732 @2x -> 824x1464 (9:16). Play caps screenshots at 2:1, so the
// tall 412x915 frame (824x1830 = 2.22:1) is NOT uploadable.
const PHONE = { viewport: { width: 412, height: 732 }, deviceScaleFactor: 2, hasTouch: true };

// ---- 1. Generate a generic 14s "episode" (night-festival mood, no text/IP) ----
const gen = await browser.newPage();
await gen.goto(BASE);
log('generating placeholder episode video (14s)…');
const videoB64 = await gen.evaluate(async () => {
  const W = 1280, H = 720;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d');
  const stars = Array.from({ length: 140 }, () => ({
    x: Math.random() * W, y: Math.random() * H * 0.62,
    r: Math.random() * 1.6 + 0.4, p: Math.random() * Math.PI * 2,
  }));
  const lanterns = Array.from({ length: 9 }, (_, i) => ({
    x: 90 + i * 140 + (i % 2) * 22, y: H * 0.66 + (i % 3) * 26, r: 17 + (i % 3) * 4,
  }));
  const start = performance.now();
  const draw = () => {
    const t = (performance.now() - start) / 1000;
    const sky = ctx.createLinearGradient(0, 0, 0, H);
    sky.addColorStop(0, '#0a0d1f'); sky.addColorStop(0.55, '#141b38'); sky.addColorStop(1, '#241a2e');
    ctx.fillStyle = sky; ctx.fillRect(0, 0, W, H);
    for (const s of stars) {
      ctx.globalAlpha = 0.35 + 0.55 * Math.abs(Math.sin(t * 1.3 + s.p));
      ctx.fillStyle = '#dfe7ff';
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
    const mg = ctx.createRadialGradient(W * 0.78, H * 0.2, 8, W * 0.78, H * 0.2, 90);
    mg.addColorStop(0, '#fff7dd'); mg.addColorStop(0.35, '#f4e8bcaa'); mg.addColorStop(1, 'transparent');
    ctx.fillStyle = mg; ctx.beginPath(); ctx.arc(W * 0.78, H * 0.2, 90, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#f5eecb'; ctx.beginPath(); ctx.arc(W * 0.78, H * 0.2, 34, 0, Math.PI * 2); ctx.fill();
    // firework bloom every 4.5s, visible for the first ~2.2s of each cycle
    const cyc = (t % 4.5) / 4.5;
    if (cyc < 0.5) {
      const fx = W * (0.24 + 0.1 * Math.sin(Math.floor(t / 4.5) * 7)), fy = H * 0.27;
      const rad = 30 + cyc * 340;
      ctx.globalAlpha = Math.max(0, 0.95 - cyc * 1.8);
      for (let i = 0; i < 30; i++) {
        const a = (i / 30) * Math.PI * 2;
        ctx.strokeStyle = i % 2 ? '#ffb46e' : '#7ecbff';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(fx + Math.cos(a) * rad * 0.55, fy + Math.sin(a) * rad * 0.55);
        ctx.lineTo(fx + Math.cos(a) * rad, fy + Math.sin(a) * rad);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }
    ctx.fillStyle = '#0b0e18';
    ctx.beginPath(); ctx.moveTo(0, H * 0.8);
    ctx.quadraticCurveTo(W * 0.3, H * 0.68, W * 0.55, H * 0.8);
    ctx.quadraticCurveTo(W * 0.8, H * 0.9, W, H * 0.78);
    ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.fill();
    ctx.strokeStyle = '#3a3350'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(0, H * 0.7);
    ctx.quadraticCurveTo(W * 0.5, H * 0.62, W, H * 0.72); ctx.stroke();
    for (const l of lanterns) {
      const glow = ctx.createRadialGradient(l.x, l.y, 2, l.x, l.y, l.r * 2.6);
      const warm = 0.75 + 0.25 * Math.sin(t * 2 + l.x);
      glow.addColorStop(0, `rgba(255,190,110,${0.85 * warm})`);
      glow.addColorStop(1, 'transparent');
      ctx.fillStyle = glow;
      ctx.beginPath(); ctx.arc(l.x, l.y, l.r * 2.6, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `rgba(255,160,80,${0.9 * warm})`;
      ctx.beginPath(); ctx.ellipse(l.x, l.y, l.r * 0.72, l.r, 0, 0, Math.PI * 2); ctx.fill();
    }
    if (t < 14.5) requestAnimationFrame(draw);
  };
  draw();
  const stream = canvas.captureStream(24);
  const rec = new MediaRecorder(stream, { mimeType: 'video/webm', videoBitsPerSecond: 4_000_000 });
  const chunks = [];
  rec.ondataavailable = (e) => chunks.push(e.data);
  const done = new Promise((res) => (rec.onstop = res));
  rec.start(500);
  await new Promise((res) => setTimeout(res, 14000));
  rec.stop();
  await done;
  const blob = new Blob(chunks, { type: 'video/webm' });
  const buf = new Uint8Array(await blob.arrayBuffer());
  let bin = '';
  for (let i = 0; i < buf.length; i += 8192) bin += String.fromCharCode(...buf.subarray(i, i + 8192));
  return btoa(bin);
});
const episodePath = `${TMP}/serifu-episode.webm`;
writeFileSync(episodePath, Buffer.from(videoB64, 'base64'));
await gen.close();
log('episode.webm written');

// Controllable fake SpeechRecognition (emits only when window.__say is called).
const fakeSpeech = () => {
  class FakeSpeechRecognition {
    constructor() { this.onresult = null; this.onerror = null; this.onend = null; }
    start() { window.__srActive = this; }
    stop() { if (window.__srActive === this) window.__srActive = null; if (this.onend) this.onend(); }
    abort() { this.stop(); }
  }
  window.SpeechRecognition = FakeSpeechRecognition;
  window.webkitSpeechRecognition = FakeSpeechRecognition;
  window.__say = (text) => {
    const sr = window.__srActive;
    if (!sr || !sr.onresult) return false;
    const result = Object.assign([{ transcript: text }], { isFinal: true });
    sr.onresult({ resultIndex: 0, results: [result] });
    return true;
  };
};

const tab = async (page, label) => page.locator(`.mnav-btn:has-text("${label}")`).first().click();

async function openTool(page, label) {
  const headerBtn = page.locator(`.room-header button:has-text("${label}")`).first();
  if (await headerBtn.isVisible().catch(() => false)) { await headerBtn.click(); return; }
  await tab(page, 'その他');
  await page.locator(`.more-actions button:has-text("${label}")`).first().click();
}

// ---- 2. User A (Aki) creates the room on a phone ----
const ctxA = await browser.newContext(PHONE);
await ctxA.addInitScript(fakeSpeech);
const pageA = await ctxA.newPage();
pageA.on('pageerror', (e) => console.log('A pageerror:', e.message));
await pageA.goto(BASE);
await pageA.fill('input[placeholder*="名前"]', 'Aki');
await pageA.click('button:has-text("Create a room")');
await pageA.waitForSelector('.room-header', { timeout: 8000 });
const roomUrl = pageA.url();
log(`room created: ${roomUrl}`);

// ---- 3. Load the original script via editor paste-import ----
await openTool(pageA, '台本');
await pageA.waitForSelector('.modal .editor-tools', { timeout: 8000 });
await pageA.click('button:has-text("paste subtitles")');
await pageA.fill('.paste-box textarea', scriptJson);
await pageA.click('.paste-box button:has-text("parse")');
await pageA.waitForSelector('.editor-line', { timeout: 8000 });
await pageA.click('.modal-footer button:has-text("apply")');
await pageA.waitForSelector('.modal', { state: 'detached', timeout: 8000 });
log('original script loaded into room');

// Show translations plainly (store shots should read instantly).
await pageA.locator('.settings-row label:has-text("訳") select').selectOption('show');

// Back to stage tab, load the local "episode" file.
await tab(pageA, 'ステージ');
await pageA.setInputFiles('.video-placeholder input[type="file"]', episodePath);
await pageA.waitForSelector('video', { timeout: 8000 });
log('video loaded');

// ---- 4. Friends join: Yui + Ren ----
async function joinFriend(name) {
  const ctx = await browser.newContext(PHONE);
  await ctx.addInitScript(fakeSpeech);
  const page = await ctx.newPage();
  await page.goto(roomUrl);
  await page.fill('input[placeholder*="名前"]', name);
  await page.click('button:has-text("Join")');
  await page.waitForSelector('.room-header', { timeout: 8000 });
  return page;
}
const pageB = await joinFriend('Yui');
const pageC = await joinFriend('Ren');
await pageA.waitForSelector('.chip.user:has-text("Ren")', { state: 'attached', timeout: 8000 });
log('3 users in room');

// ---- 5. Claim characters ----
await pageA.locator('.char-pill:has-text("アオイ")').first().click();
await pageB.locator('.char-pill:has-text("レン")').first().click();
await pageC.locator('.char-pill:has-text("ユキ")').first().click();
await pageA.waitForSelector('.char-pill:has-text("ユキ")[disabled]', { timeout: 8000 }).catch(() => log('warn: claim sync wait failed'));
log('characters claimed');

// ---- 6. Shot 03 — together (stage: firework frame, synced controls, cast) ----
await pageA.click('.play-btn');
await pageA.waitForTimeout(1400);
await pageA.click('.play-btn'); // pause on the firework
await pageA.waitForTimeout(700);
await pageA.screenshot({ path: `${OUT}/03-together-sync.png` });
log('shot 03 saved');

// ---- 7. Shot 04 — script tab with furigana + visible translations ----
await tab(pageA, '台本');
await pageA.waitForSelector('.line', { timeout: 8000 });
await pageA.waitForTimeout(400);
await pageA.screenshot({ path: `${OUT}/04-script-furigana.png` });
log('shot 04 saved');

// ---- 8. Shot 05 — script editor (import + speaker tagging) ----
await openTool(pageA, '台本');
await pageA.waitForSelector('.editor-line', { timeout: 8000 });
await pageA.waitForTimeout(400);
await pageA.screenshot({ path: `${OUT}/05-import-editor.png` });
await pageA.click('.modal-footer button:has-text("cancel")').catch(async () => {
  await pageA.click('.modal-header button');
});
await pageA.waitForSelector('.modal', { state: 'detached', timeout: 8000 });
log('shot 05 saved');

// ---- 9. Rehearsal: play from 0, auto-pause at Aki's line (t=5) ----
await tab(pageA, 'ステージ');
await pageA.click('button:has-text("↺5")');
await pageA.waitForTimeout(300);
await pageA.click('.play-btn');
await pageA.waitForSelector('.rehearsal-banner', { timeout: 20000 });
await pageA.waitForSelector('.mic-live', { timeout: 8000 });
await pageA.waitForTimeout(350);
await pageA.screenshot({ path: `${OUT}/01-hero-your-line.png` });
log('shot 01 saved');

// ---- 10. Shot 02 — the pass badge (imperfect but passing attempt) ----
const said = await pageA.evaluate(() => window.__say('夏祭りの準備手伝ってくれる'));
if (!said) log('warn: __say found no active recognizer');
await pageA.waitForSelector('.score-badge.pass', { timeout: 8000 });
await pageA.screenshot({ path: `${OUT}/02-score-pass.png` });
const badge = await pageA.textContent('.score-badge.pass').catch(() => null);
log(`shot 02 saved (badge: ${badge})`);
await pageA.waitForSelector('.rehearsal-banner', { state: 'detached', timeout: 8000 }).catch(() => {});
await pageA.click('.play-btn').catch(() => {});

// ---- 11. Shot 08 — episode browser, filled via the UI with neutral titles ----
await openTool(pageA, '話数');
await pageA.waitForSelector('.season-label', { timeout: 8000 });
const epTitles = ['夏祭りの夜', '流れ星の丘', '海辺の手紙', '雨宿りの音'];
const inputs = pageA.locator('.ep-title');
const n = Math.min(epTitles.length, await inputs.count());
for (let i = 0; i < n; i++) await inputs.nth(i).fill(epTitles[i]);
await pageA.waitForTimeout(400);
await pageA.screenshot({ path: `${OUT}/08-episode-browser.png` });
log('shot 08 saved');

// ---- 12. Shots 06 + 07 — solo practice, then mastery seeded by solo passes ----
const ctxM = await browser.newContext(PHONE);
await ctxM.addInitScript(fakeSpeech);
const pageM = await ctxM.newPage();
pageM.on('pageerror', (e) => console.log('M pageerror:', e.message));
await pageM.goto(`${BASE}/#/p/flower-field`);
await pageM.waitForSelector('.solo-line', { timeout: 8000 });
// line 3 has no character names in text or translation
await pageM.click('.solo-nav button:has-text("skip →")');
await pageM.click('.solo-nav button:has-text("skip →")');
await pageM.click('.hide-levels button:has-text("ふりがな無し")');
// the speaker label is a licensed character name — blur it for the store asset
await pageM.addStyleTag({ content: '.solo-who{filter: blur(9px);}' });
await pageM.waitForTimeout(400);
await pageM.screenshot({ path: `${OUT}/06-solo-practice.png` });
log('shot 06 saved');

// Pass the first four lines by "speaking" them — feeds the mastery ledger
// with neutral vocab/grammar (花畑, 別に, 君, 笑う, 〜てくれない？ …).
await pageM.reload();
await pageM.waitForSelector('.solo-line', { timeout: 8000 });
const soloTexts = [
  'フリーレンあの花畑を出す魔法見せてくれない',
  '別に大した魔法じゃないよ',
  'でも君はその魔法を使うのが好きなんだろう',
  'もし笑われたらどうするの',
];
for (const t of soloTexts) {
  await pageM.waitForSelector('.mic-live', { timeout: 8000 });
  const ok = await pageM.evaluate((x) => window.__say(x), t);
  if (!ok) log('warn: solo __say failed');
  await pageM.waitForTimeout(900);
}
log('solo passes recorded');

// Open a room just to reach the mastery panel UI.
await pageM.goto(`${BASE}/#/`);
await pageM.fill('input[placeholder*="名前"]', 'Mio');
await pageM.click('button:has-text("Create a room")');
await pageM.waitForSelector('.room-header', { timeout: 8000 });
await openTool(pageM, '習得');
await pageM.waitForSelector('.mastery-row', { timeout: 8000 });
await pageM.click('button:has-text("▶ review")');
await pageM.waitForSelector('.review-front', { timeout: 8000 });
await pageM.click('button:has-text("show answer")');
await pageM.waitForTimeout(400);
await pageM.screenshot({ path: `${OUT}/07-mastery-review.png` });
log('shot 07 saved');
await ctxM.close();

// ---- 13. Shot 09 — landing (third demo chip carries an IP name → blurred) ----
const ctxL = await browser.newContext(PHONE);
const pageL = await ctxL.newPage();
await pageL.goto(BASE);
await pageL.waitForSelector('.solo-links .chip', { timeout: 8000 });
await pageL.addStyleTag({
  content: '.solo-links .row a.chip:nth-child(3){filter: blur(7px);}',
});
await pageL.waitForTimeout(600);
await pageL.screenshot({ path: `${OUT}/09-landing.png` });
log('shot 09 saved');
await ctxL.close();

await browser.close();
log('done');
