// v5/lib/stealth.mjs — smarter anti-detection for Playwright.
//
// Upgrades over v4's Selenium + CDP one-liner (Object.defineProperty on
// navigator.webdriver). We build a Playwright BrowserContext that:
//   1. rotates a modern Desktop Chrome user-agent + matching client hints,
//   2. injects an init script BEFORE any page script runs to patch the
//      common bot-detection surface (webdriver, plugins, languages,
//      window.chrome, permissions.query, WebGL vendor strings, iframe
//      contentWindow leaks),
//   3. randomizes viewport, timezone, locale, and color scheme,
//   4. persists storageState so cookies/local-storage survive runs,
//   5. exposes human-like helpers (move cursor, scroll, read-pause).

import fs from 'node:fs';
import path from 'node:path';

// Small rotation pool — all modern Chrome on macOS/Windows. We lean on
// matching sec-ch-ua hints so the UA claim is internally consistent.
const UA_POOL = [
  {
    ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    platform: 'MacIntel',
    secChUa: '"Chromium";v="129", "Not=A?Brand";v="8", "Google Chrome";v="129"',
    secChUaPlatform: '"macOS"',
  },
  {
    ua: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    platform: 'Win32',
    secChUa: '"Chromium";v="129", "Not=A?Brand";v="8", "Google Chrome";v="129"',
    secChUaPlatform: '"Windows"',
  },
  {
    ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    platform: 'MacIntel',
    secChUa: '"Chromium";v="128", "Not=A?Brand";v="24", "Google Chrome";v="128"',
    secChUaPlatform: '"macOS"',
  },
];

const VIEWPORTS = [
  { width: 1920, height: 1080 },
  { width: 1680, height: 1050 },
  { width: 1536, height: 960 },
  { width: 1440, height: 900 },
];

const TIMEZONES = ['America/Los_Angeles', 'America/New_York', 'America/Chicago'];

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

// Init script injected before any page JS runs. Must be self-contained (no
// closures over Node globals).
const INIT_SCRIPT = `
(() => {
  // webdriver flag — most common headless tell.
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

  // Plugins + mimeTypes length. Headless Chrome reports 0; real Chrome has 3+.
  const fakePlugin = (name) => ({ name, filename: name + '.plugin', description: '' });
  const plugins = [
    fakePlugin('Chrome PDF Plugin'),
    fakePlugin('Chrome PDF Viewer'),
    fakePlugin('Native Client'),
  ];
  Object.defineProperty(navigator, 'plugins', {
    get: () => Object.assign(plugins, { item: (i) => plugins[i], namedItem: () => null }),
  });

  // Languages must be a non-empty array.
  Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

  // window.chrome — headless lacks this.
  if (!window.chrome) {
    window.chrome = { runtime: {}, loadTimes: () => ({}), csi: () => ({}), app: {} };
  }

  // permissions.query('notifications') returns 'denied' in headless vs 'prompt'
  // in real Chrome. Patch it to match the user's notification state.
  const origQuery = window.navigator.permissions && window.navigator.permissions.query;
  if (origQuery) {
    window.navigator.permissions.query = (params) =>
      params && params.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : origQuery(params);
  }

  // WebGL vendor/renderer — real Chrome returns a GPU string. Spoof to a
  // common Intel chipset rather than SwiftShader.
  const getParameter = WebGLRenderingContext.prototype.getParameter;
  WebGLRenderingContext.prototype.getParameter = function (p) {
    if (p === 37445) return 'Intel Inc.';                     // UNMASKED_VENDOR_WEBGL
    if (p === 37446) return 'Intel Iris OpenGL Engine';        // UNMASKED_RENDERER_WEBGL
    return getParameter.call(this, p);
  };

  // hardwareConcurrency + deviceMemory — some fingerprinters flag 1/0.
  try { Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 }); } catch {}
  try { Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 }); } catch {}
})();
`;

/**
 * Launch a Playwright Chromium context that looks like a real Chrome session.
 *
 * @param {import('playwright').BrowserType} chromium
 * @param {object} opts
 * @param {boolean} [opts.headless]     default true
 * @param {string}  [opts.storageState] path to storageState JSON (cookies); if
 *                                      missing, context starts clean
 * @param {string}  [opts.runDir]       if set, screenshots on failure land here
 */
export async function launchStealthContext(chromium, opts = {}) {
  const headless = opts.headless ?? true;
  const ident = pick(UA_POOL);
  const viewport = pick(VIEWPORTS);
  const timezoneId = pick(TIMEZONES);

  const browser = await chromium.launch({
    headless,
    args: [
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process',
      `--window-size=${viewport.width},${viewport.height}`,
    ],
  });

  const contextOptions = {
    userAgent: ident.ua,
    viewport,
    locale: 'en-US',
    timezoneId,
    colorScheme: 'light',
    deviceScaleFactor: 1 + Math.random() * 0.5, // 1.0–1.5, mimics real DPI
    extraHTTPHeaders: {
      'sec-ch-ua': ident.secChUa,
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': ident.secChUaPlatform,
      'accept-language': 'en-US,en;q=0.9',
    },
  };

  if (opts.storageState && fs.existsSync(opts.storageState)) {
    contextOptions.storageState = opts.storageState;
  }

  const context = await browser.newContext(contextOptions);
  await context.addInitScript(INIT_SCRIPT);

  // Stash metadata for callers that want to log the identity used.
  context._v5 = { ident, viewport, timezoneId };

  return { browser, context };
}

/** Save cookies + localStorage for next run. Never throws. */
export async function persistStorageState(context, storageStatePath) {
  try {
    fs.mkdirSync(path.dirname(storageStatePath), { recursive: true });
    await context.storageState({ path: storageStatePath });
    return true;
  } catch {
    return false;
  }
}
