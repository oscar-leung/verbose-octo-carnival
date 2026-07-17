// Full browser E2E demo of Serifu: two users, room join, demo script,
// character claims, synced playback, rehearsal auto-pause, voice chat.
import { chromium } from 'playwright-core';
import { mkdirSync, writeFileSync } from 'node:fs';

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
  args: [
    '--autoplay-policy=no-user-gesture-required',
    '--use-fake-ui-for-media-stream',
    '--use-fake-device-for-media-stream',
    '--no-sandbox',
  ],
});

// ---- 1. Generate a ~12s test "episode" via canvas + MediaRecorder ----
const genPage = await browser.newPage();
await genPage.goto(BASE);
const videoB64 = await genPage.evaluate(async () => {
  const canvas = document.createElement('canvas');
  canvas.width = 640;
  canvas.height = 360;
  const ctx = canvas.getContext('2d');
  const start = performance.now();
  const draw = () => {
    const t = (performance.now() - start) / 1000;
    const g = ctx.createLinearGradient(0, 0, 640, 360);
    g.addColorStop(0, `hsl(${(t * 30) % 360}, 45%, 22%)`);
    g.addColorStop(1, '#101018');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 640, 360);
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 64px sans-serif';
    ctx.fillText(`${t.toFixed(1)}s`, 240, 200);
    if (t < 12.5) requestAnimationFrame(draw);
  };
  draw();
  const stream = canvas.captureStream(15);
  const rec = new MediaRecorder(stream, { mimeType: 'video/webm' });
  const chunks = [];
  rec.ondataavailable = (e) => chunks.push(e.data);
  const done = new Promise((res) => (rec.onstop = res));
  rec.start(500);
  await new Promise((res) => setTimeout(res, 12000));
  rec.stop();
  await done;
  const blob = new Blob(chunks, { type: 'video/webm' });
  const buf = await blob.arrayBuffer();
  let bin = '';
  const bytes = new Uint8Array(buf);
  for (let i = 0; i < bytes.length; i += 8192) {
    bin += String.fromCharCode(...bytes.subarray(i, i + 8192));
  }
  return btoa(bin);
});
const episodePath = `${SHOTS}/../episode.webm`;
writeFileSync(episodePath, Buffer.from(videoB64, 'base64'));
check('generated test episode video', videoB64.length > 10000);
await genPage.close();

// ---- 2. User A creates a room ----
const ctxA = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const pageA = await ctxA.newPage();
pageA.on('pageerror', (e) => console.log('A pageerror:', e.message));
await pageA.goto(BASE);
await pageA.screenshot({ path: `${SHOTS}/01-landing.png` });
await pageA.fill('input[placeholder*="名前"]', 'Oscar');
await pageA.click('button:has-text("Create a room")');
await pageA.waitForURL(/#\/r\//, { timeout: 5000 });
await pageA.waitForSelector('.room-header', { timeout: 5000 });
const roomUrl = pageA.url();
check('user A created + joined room', /#\/r\/[a-z0-9]+/.test(roomUrl));

// ---- 3. User B joins via the link ----
const ctxB = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const pageB = await ctxB.newPage();
pageB.on('pageerror', (e) => console.log('B pageerror:', e.message));
await pageB.goto(roomUrl);
await pageB.fill('input[placeholder*="名前"]', 'Yuki');
await pageB.click('button:has-text("Join")');
await pageB.waitForSelector('.room-header', { timeout: 5000 });
await pageA.waitForSelector('.chip.user:has-text("Yuki")', { timeout: 5000 });
check('user B joined; A sees both users', true);

// ---- 4. Load the demo script from the empty state ----
await pageA.click('button:has-text("load demo scene")');
await pageA.waitForSelector('.script-header h2', { timeout: 5000 });
await pageB.waitForSelector('.script-header h2', { timeout: 5000 });
const titleB = await pageB.textContent('.script-header h2');
check('demo script broadcast to both users', (titleB ?? '').includes('フリーレン'));

// ---- 5. Claim characters ----
await pageA.click('.char-pill:has-text("ハイター")');
await pageB.waitForSelector('.char-pill:has-text("ハイター")[disabled]', { timeout: 5000 });
await pageB.click('.char-pill:has-text("ヒンメル")');
await pageA.waitForSelector('.char-pill:has-text("ヒンメル")[disabled]', { timeout: 5000 });
check('character claims sync both ways', true);

// ---- 6. A loads their local "episode" file ----
await pageA.setInputFiles('.video-placeholder input[type="file"]', episodePath);
await pageA.waitForSelector('video', { timeout: 5000 });
await pageA.screenshot({ path: `${SHOTS}/02-room-ready.png` });
check('A loaded local video file', true);

// ---- 7. Play: expect rehearsal auto-pause at Heiter line (t=5s) ----
await pageA.click('.play-btn');
await pageB.waitForSelector('.play-btn:has-text("⏸")', { timeout: 5000 });
check('play propagates to B', true);

await pageA.waitForSelector('.rehearsal-banner', { timeout: 15000 });
await pageB.waitForSelector('.rehearsal-banner', { timeout: 5000 });
const bannerText = await pageA.textContent('.rehearsal-banner');
check('rehearsal auto-pause fired at claimed line on BOTH clients',
  (bannerText ?? '').includes('ハイター') && (bannerText ?? '').includes('Oscar'));
await pageA.screenshot({ path: `${SHOTS}/03-rehearsal-pause-A.png` });
await pageB.screenshot({ path: `${SHOTS}/04-rehearsal-pause-B.png` });

// Active line should be highlighted in the script panel.
const activeLine = await pageB.$('.line.active');
check('active line highlighted in script panel', activeLine !== null);

// ---- 8. Continue after "saying" the line ----
await pageA.click('.rehearsal-banner button.primary');
await pageA.waitForSelector('.rehearsal-banner', { state: 'detached', timeout: 5000 });
await pageB.waitForSelector('.rehearsal-banner', { state: 'detached', timeout: 5000 });
const playing = await pageB.textContent('.play-btn');
check('resume clears banner everywhere and playback continues', playing === '⏸');

// ---- 9. Voice chat between the two users ----
await pageA.click('button:has-text("join voice")');
await pageB.click('button:has-text("join voice")');
await pageA.waitForSelector('.voice-panel:has-text("1 other")', { timeout: 10000 });
await pageB.waitForSelector('.voice-panel:has-text("1 other")', { timeout: 10000 });
// Give the mesh a moment, then check the RTCPeerConnection actually connected.
await pageA.waitForFunction(
  () => document.querySelectorAll('audio').length >= 1,
  { timeout: 10000 }
).catch(() => null);
const audioCountA = await pageA.evaluate(() => document.querySelectorAll('audio').length);
check('voice mesh delivered a remote audio stream', audioCountA >= 1);
await pageA.waitForSelector('.chip.user:has-text("🎙")', { timeout: 5000 });
check('voice presence badges visible', true);

// ---- 10. Mute state propagates ----
await pageA.click('button:has-text("mute")');
await pageB.waitForSelector('.chip.user:has-text("🔇")', { timeout: 5000 });
check('mute state propagates to peer roster', true);
await pageB.screenshot({ path: `${SHOTS}/05-voice-connected-B.png` });

// ---- 11. Script editor opens with the demo lines ----
await pageA.click('.room-header button:has-text("台本")');
await pageA.waitForSelector('.editor-line', { timeout: 5000 });
const editorLines = await pageA.$$eval('.editor-line', (els) => els.length);
check('editor shows all 12 demo lines', editorLines === 12);
await pageA.screenshot({ path: `${SHOTS}/06-editor.png` });
await pageA.click('.modal-footer button:has-text("cancel")');

// ---- 12. Seek via script line click ----
await pageB.click('.line >> nth=0 >> .line-time');
await pageA.waitForFunction(() => {
  const v = document.querySelector('video');
  return v && Math.abs(v.currentTime - 5) < 2;
}, { timeout: 5000 });
check('clicking a line seeks everyone there', true);

console.log('---');
for (const [label, ok] of results) if (!ok) console.log('FAILED:', label);
console.log(`${results.filter(([, ok]) => ok).length}/${results.length} checks passed`);
await browser.close();
process.exit(process.exitCode ?? 0);
