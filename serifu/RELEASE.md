# Serifu — Release Runbook

Serifu ships from one codebase to three surfaces. The web app is the product;
phones get it as an installable PWA today, with a documented path to the real
App Store / Play Store when you want it.

## 1. Website (live today)

Render auto-deploys `main` using the repo's `render.yaml`.

Checklist per release:

1. Merge the release PR into `main`.
2. Watch the deploy in the Render dashboard (build ~2–4 min).
3. Verify `https://<your-app>.onrender.com/healthz` returns `{"ok":true}`.
4. Smoke it: create a room on your phone + laptop, load the demo scene, play.

Optional but recommended:

- **Custom domain** (Render → Settings → Custom Domains) — nicer links for
  friends, and required later for a Play Store TWA.
- **TURN for voice** — set `TURN_URLS` / `TURN_USERNAME` / `TURN_CREDENTIAL`
  env vars (free tier at metered.ca) if two friends ever can't hear each other.
- Upgrade off the free plan (~$7/mo) to remove the ~30–60 s cold start.

## 2. Android

**Today (no store, 30 seconds):** open the site in Chrome → ⋮ menu →
*Add to Home screen* → *Install*. Because Serifu is a PWA (manifest + service
worker + icons), Android installs it as a real app: own icon, standalone
window, full mic/speech/WebRTC support.

**Play Store (when ready):** package the PWA as a Trusted Web Activity with
[Bubblewrap](https://github.com/GoogleChromeLabs/bubblewrap):

```bash
npm i -g @bubblewrap/cli
bubblewrap init --manifest https://<your-domain>/manifest.webmanifest
bubblewrap build        # produces an .aab
```

Requirements: a Google Play developer account ($25 one-time), a custom domain
serving `/.well-known/assetlinks.json` (bubblewrap generates it), and the
standard store listing (screenshots, privacy policy). The app itself needs no
changes — TWA runs the live site, so web deploys update the "app" instantly.

## 3. iOS

**Today (no store):** open the site in Safari → Share → *Add to Home Screen*.
It launches standalone with the Serifu icon and dark theme. Everything works
except speech *scoring* — iOS Safari has no Web Speech recognition, so iPhone
players read their line aloud and tap continue (the app detects this and
adjusts its hints). Voice chat and synced playback work fully (iOS 14.3+).

**App Store (when ready):** wrap with [Capacitor](https://capacitorjs.com):

```bash
npm i @capacitor/core @capacitor/cli
npx cap init serifu app.serifu --web-dir dist
npx cap add ios && npx cap open ios
```

Requirements: a Mac with Xcode, an Apple Developer account ($99/yr), mic
permission strings in `Info.plist` (`NSMicrophoneUsageNotice`), and App Store
review. Note: speech recognition inside an iOS WKWebView still isn't
available — a native App Store build would want Apple's `SFSpeechRecognizer`
bridged in, which is the one genuinely native piece of future work.

## Content reminder

Ship the app, not the anime. Serifu contains no episode video or full
transcripts — players load their own files and import their own subtitles.
Keep it that way for anything public; the bundled demo scene is a short
approximate excerpt for onboarding only.

## Release checklist (any platform)

- [ ] `npm run typecheck && npm test` — all green
- [ ] `npm run build` then `PORT=4123 npm start` + `npm run e2e` — 19/19
- [ ] Version bumped in `package.json`
- [ ] Merged to `main`, Render deploy green, `/healthz` ok
- [ ] Quick two-device smoke (one phone, one laptop)
