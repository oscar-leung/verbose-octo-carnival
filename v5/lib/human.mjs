// v5/lib/human.mjs — human-like timing and interaction helpers.
//
// All waits + pointer moves go through here so the scraper never has raw
// setTimeout or page.mouse.move calls scattered around. Centralising the
// random ranges also makes it easy to dial cadence up or down per run.

export function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

export function randFloat(min, max) {
  return min + Math.random() * (max - min);
}

export function randInt(min, max) {
  return Math.floor(randFloat(min, max + 1));
}

/** Quick distracted glance — 0.4–1.5s. */
export async function humanWait(minS = 0.4, maxS = 1.5) {
  await sleep(randFloat(minS, maxS) * 1000);
}

/** Post-apply cooldown — 8–18s (matches v4). */
export async function postApplyWait() {
  await sleep(randFloat(8, 18) * 1000);
}

/** Session break every N applies — 60–120s (matches v4). */
export async function sessionBreak() {
  await sleep(randFloat(60, 120) * 1000);
}

/**
 * Move the mouse along a jittery bezier-ish path from the current position
 * (assumed center of viewport) to (x, y). Playwright's mouse.move supports
 * a `steps` arg but does a straight line; we synthesise small detours.
 */
export async function humanMoveTo(page, x, y, steps = 20) {
  const viewport = page.viewportSize() || { width: 1280, height: 800 };
  let curX = viewport.width / 2;
  let curY = viewport.height / 2;
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    // ease-in-out with small perpendicular jitter
    const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    const jitter = (Math.random() - 0.5) * 6;
    const nx = curX + (x - curX) * ease + jitter;
    const ny = curY + (y - curY) * ease + jitter;
    await page.mouse.move(nx, ny);
    await sleep(randInt(5, 18));
  }
  await page.mouse.move(x, y);
}

/** Scroll the page in human-sized increments until predicate() resolves true
 *  or maxScrolls is reached. Returns whether the predicate was satisfied. */
export async function humanScrollUntil(page, predicate, { maxScrolls = 12 } = {}) {
  for (let i = 0; i < maxScrolls; i++) {
    if (await predicate()) return true;
    const delta = randInt(280, 520);
    await page.mouse.wheel(0, delta);
    await sleep(randInt(350, 900));
  }
  return predicate();
}

/** Type with per-keystroke jitter. Playwright's page.type() has a `delay`
 *  option but it's uniform; real typing isn't. */
export async function humanType(locator, text, { meanMs = 80 } = {}) {
  await locator.click();
  await humanWait(0.2, 0.5);
  for (const ch of text) {
    await locator.page().keyboard.type(ch);
    await sleep(randFloat(meanMs * 0.5, meanMs * 1.5));
  }
}
