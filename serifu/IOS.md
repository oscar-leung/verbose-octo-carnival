# iOS / App Store runbook

**Store state: not started** — track here as: not started → building → TestFlight →
submitted → in review → live / rejected (+ reason).

The App Store app is a Capacitor wrapper: a thin native shell whose WKWebView loads
the live site. Web deploys update the "app" instantly — the store package only
changes when the wrapper itself does (icon, permissions, plugins).

Oscar's parts are marked 🧑 (they need your Apple ID, your Mac, your card); Claude's
are marked 🤖 (already done or one-message turnaround).

## 0. Prerequisites

Already have:
- 🤖 PWA (manifest, service worker, dark theme) — shipped
- 🤖 Icons: `public/icon-512.png`, `public/apple-touch-icon.png` — store-icon ready
- 🤖 `/privacy.html` — Apple requires a working privacy-policy URL
- 🧑 Custom domain live on Render (same one as ANDROID.md step 1–2)

Still need:
- 🧑 A Mac (any Apple-silicon Mac; Xcode requires macOS — no way around this)
- 🧑 Xcode (free, ~15 GB): App Store on the Mac → search "Xcode" → install
- 🧑 Apple Developer Program membership — **$99/yr** (step 1)

## 1. 🧑 Apple Developer Program (~20 min + up to 48 h approval)

1. Go to **developer.apple.com/programs/enroll** → sign in with your Apple ID
   (create one at appleid.apple.com if needed; turn on two-factor — required).
2. Enroll as **Individual** (not Organization — no D-U-N-S number needed).
   Your legal name becomes the "seller" name on the listing; that's fine.
3. Pay **$99/yr**, auto-renew on. Approval email usually arrives within 48 h.
4. While waiting: confirm you can sign in at **appstoreconnect.apple.com**.

## 2. 🧑 Package with Capacitor (~30 min, in the serifu/ repo on your Mac)

```bash
npm i @capacitor/core @capacitor/cli   # runtime + CLI, saved to package.json
npx cap init Serifu com.oscarleung.serifu --web-dir dist
                                       # writes capacitor.config.ts (app name,
                                       # bundle id — keep it matching Android)
npm run build                          # produces dist/ (cap requires it to exist)
npx cap add ios                        # generates the ios/ Xcode project
npx cap sync                           # copies dist/ + plugin config into ios/
npx cap open ios                       # opens ios/App/App.xcworkspace in Xcode
```

**Live site vs bundled dist.** By default Capacitor serves the copied `dist/`
from inside the app — features then ship only when you rebuild and resubmit the
wrapper. Instead, point the shell at the live site by editing
`capacitor.config.ts`:

```ts
const config: CapacitorConfig = {
  appId: 'com.oscarleung.serifu',
  appName: 'Serifu',
  webDir: 'dist',
  server: { url: 'https://YOUR-DOMAIN', allowNavigation: ['YOUR-DOMAIN'] },
};
```

Trade-off: `server.url` means every web deploy updates the app instantly (same
model as the Android TWA) but the app needs a network connection at launch;
bundled `dist` works offline-ish but goes stale. **Recommendation: `server.url`.**
Serifu is a multiplayer app — it needs the network anyway, and one release
cadence (web) beats two. Run `npx cap sync` after any config change.

🤖 Claude can write `capacitor.config.ts` and the package.json changes in a PR;
only the Mac-side `cap add ios` / Xcode steps must run on your machine.

## 3. 🧑 Xcode configuration (~20 min)

In Xcode with `App.xcworkspace` open, select the **App** target:

1. **Signing & Capabilities** → check "Automatically manage signing" → Team:
   your name (appears once step 1 is approved). Bundle Identifier:
   `com.oscarleung.serifu`.
2. **Info** tab → add key `NSMicrophoneUsageDescription` (shows as "Privacy —
   Microphone Usage Description") with value:
   `Voice chat and pronunciation practice`.
   Without this string the app crashes on first mic request and review rejects it.
3. **App icon**: open `ios/App/App/Assets.xcassets` → AppIcon → drag
   `public/icon-512.png` in. Xcode 15+ accepts a single 1024×1024 image; if it
   wants 1024, upscale: `sips -z 1024 1024 public/icon-512.png --out icon-1024.png`.
   The icon must have no alpha channel for the store — export as opaque PNG.
4. **General** → Minimum Deployments: **iOS 15.0** (Capacitor 6/7 floor;
   WebRTC + getUserMedia in WKWebView are solid from 14.3+, so 15 is safe).
5. Build once (⌘B) to confirm signing works.

## 4. 🧑 Test on your own iPhone (free, ~10 min)

1. Plug in your iPhone (or same-Wi-Fi wireless debugging) → select it as the
   run destination → press ▶. First run: iPhone Settings → General → VPN &
   Device Management → trust your developer certificate.
2. Smoke test: create a room with a friend, load a scene, confirm voice chat
   connects, mic permission prompt shows your usage string, playback syncs,
   and the "read aloud + continue" fallback appears at your lines (see §7).

## 5. 🧑 TestFlight (~30 min + ~1 day first-build review)

1. **appstoreconnect.apple.com** → My Apps → **+** → New App → platform iOS,
   name `Serifu`, primary language English, bundle ID `com.oscarleung.serifu`,
   SKU `serifu-ios`.
2. Xcode: set the destination to "Any iOS Device (arm64)" → **Product →
   Archive** → in the Organizer window, **Distribute App → App Store Connect →
   Upload**. Accept defaults.
3. App Store Connect → your app → **TestFlight** tab. The build appears after
   processing (~15 min). Answer the export-compliance question: the app uses
   only standard HTTPS/WebRTC encryption → "standard encryption, exempt".
4. **Internal testing**: add up to 100 testers by their Apple-ID emails — they
   get a TestFlight invite instantly, no review. (External testing links need a
   one-time beta review, ~1 day.)
5. Run a real session with friends before submitting to the store.

## 6. 🧑 App Store submission (~1 h + 1–3 days review)

App Store Connect → your app → the iOS version page:

- **Name**: `Serifu` · **Subtitle** (30 chars): `Watch-party language practice`
- **Category**: Education · **Price**: Free
- **Description / keywords / promo text**: ask Claude 🤖 — store-ready,
  anime-agnostic copy on request (mirrors the Play listing).
- **Screenshots** (🤖 Claude generates on request): required sizes are
  **6.9" iPhone — 1320×2868** (1290×2796 also accepted), and if you enable
  iPad, **13" iPad — 2064×2752**. Apple auto-scales these to smaller devices;
  no other sizes needed. Simplest path: iPhone-only for v1 (uncheck iPad in
  Xcode General → Supported Destinations) — one screenshot set.
- **Privacy Policy URL**: `https://YOUR-DOMAIN/privacy.html`
- **Age rating**: answer the questionnaire all-"None" → results in **4+**.
  (User-loaded media is local-only, like a video player; no UGC hosting.)
- **App Privacy** (Nutrition Label) — must match privacy.html exactly:
  - "Do you collect data from this app?" → **No, we do not collect data.**
    That is the whole label: no accounts, no analytics, no ads, no tracking;
    room state is transient in-memory relay, not collection linked to identity.
    Mic audio is processed locally / peer-to-peer and never reaches our server.
  - If Apple's flow forces detail: Audio Data — used for App Functionality,
    **not linked to identity**, **not used for tracking**, not collected/stored.
- **Review notes** (paste something like): "Serifu is a language-practice
  watch-party tool. Users bring their own local video files — the app ships no
  third-party media and never uploads user media; only playback timing syncs
  between friends. No account needed. To test: open the app, create a room,
  load the bundled demo scene, tap a character's line to see rehearsal mode.
  Microphone is used for peer-to-peer voice chat and pronunciation practice."
- **Submit for Review**. Typical turnaround 24–72 h. Log the outcome in the
  store-state line at the top of this file; if rejected, record the guideline
  number and reason before changing anything.

## 7. Platform gap to disclose honestly

iOS WKWebView has **no Web Speech recognition**, so speech *scoring* doesn't
run on iPhone: the app detects this and shows the read-aloud-then-tap-continue
flow instead (already shipped). Voice chat, sync, furigana, wordbook, and
mastery all work fully. Say so plainly in the description ("On iPhone, read
your line aloud and tap continue — automatic scoring is coming") — overstating
it invites 2.3.1 metadata-accuracy rejections and bad reviews.

Future path: a small Capacitor plugin bridging Apple's **SFSpeechRecognizer**
— a Swift class exposing start/stop-recognition to JS, returning the ja-JP
transcript to the existing scoring code in `client/src/lib/`, plus the
`NSSpeechRecognitionUsageDescription` Info.plist string and a privacy-label
update (still App Functionality, on-device recognition available). Roughly a
week of native work; do it after the wrapper is live and stable.

## 8. Compliance warnings

- **IP / branding**: the listing (name, icon, screenshots, description,
  keywords) stays 100% anime-agnostic. No Frieren name, artwork, or episode
  frames anywhere store-facing — Apple asks for proof of rights on third-party
  IP (guideline 5.2) and unlicensed use means rejection or takedown. Frieren
  remains your private use case. See RELEASE.md "Going commercial".
- **Guideline 4.2 (minimum functionality)**: Apple rejects "just a website"
  wrappers. Serifu clears it on substance — real-time multiplayer sync rooms,
  peer-to-peer voice chat, mic-driven rehearsal, spaced-repetition wordbook —
  but help the reviewer see that: review notes explaining the room flow, and
  screenshots showing the app doing things no webpage-in-a-tab does. If 4.2 is
  ever cited anyway, the SFSpeechRecognizer plugin (§7) is the strongest
  native-integration answer.
- **Privacy honesty**: the Nutrition Label, privacy.html, and the app's actual
  behavior must agree. Any future change (analytics, accounts, hosted scripts)
  updates all three in the same PR — 🤖 Claude keeps them in sync; flag changes
  to store-ops.
- **Yearly reality**: the $99 renews annually; a lapsed membership pulls the
  app from sale (existing installs keep working).
