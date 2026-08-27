# Android / Play Store runbook

The Play Store app is a Trusted Web Activity (TWA): a thin, store-installable
wrapper around the live website. Web deploys update the "app" instantly — you
ship the store package once.

Oscar's parts are marked 🧑; Claude's are marked 🤖 (already done or
one-message turnaround).

## 0. Prerequisites (done)

- 🤖 PWA manifest, service worker, icons — shipped
- 🤖 `/privacy.html` — Play requires a working privacy-policy URL
- 🤖 `/.well-known/assetlinks.json` served (placeholder fingerprint, see step 4)

## 1. 🧑 Buy the domain (~10 min, ~$10–14/yr)

TWA requires your own domain (onrender.com subdomains can't prove ownership).

1. Go to **porkbun.com** (simple, honest pricing; Cloudflare Registrar is the
   at-cost alternative if you already use Cloudflare).
2. Search your candidate name. Suggested, in order:
   `serifu.app` → `serifu.dev` → `serifu.live` → `getserifu.com` →
   `serifu.study`. (.app/.dev enforce HTTPS — fine, Render provides it.)
3. Add to cart → check out. Skip all upsells (hosting, email, SSL — not
   needed). Auto-renew: on.

## 2. 🧑 Point the domain at Render (~10 min + DNS wait)

1. Render dashboard → **serifu** service → Settings → **Custom Domains** →
   Add `serifu.app` (and `www.serifu.app`).
2. Render shows exactly which DNS records to create (an A/ALIAS record for
   the apex, a CNAME for www). Copy them.
3. Porkbun → your domain → **DNS** → add those records verbatim.
4. Wait for Render's green "verified" check (minutes to ~1 hour). HTTPS is
   automatic. Confirm `https://YOUR-DOMAIN/healthz` returns `{"ok":true}`.

## 3. 🧑 Play Console account (~15 min + verification wait)

1. **play.google.com/console** → sign in with your Google account →
   "Create developer account" → **personal** account type.
2. Pay the **$25 one-time** fee. Complete identity verification (may take
   1–2 days — start this early; you can do step 4 while waiting).

## 4. 🧑 Package the app with Bubblewrap (~30 min, on your Mac/PC)

Needs Node 18+. Bubblewrap offers to download the JDK and Android SDK itself —
say yes.

```bash
npm i -g @bubblewrap/cli
mkdir serifu-twa && cd serifu-twa
bubblewrap init --manifest https://YOUR-DOMAIN/manifest.webmanifest
```

Prompt answers:
- Domain: `YOUR-DOMAIN` · App name: `Serifu` · Short name: `Serifu`
- Application ID: `com.oscarleung.serifu` (must match assetlinks.json)
- Display mode `standalone`, orientation `default`, status bar `#0e1014`
- Icons: accept the ones from the manifest
- Signing key: let it create one. **Back up the `.keystore` file and both
  passwords somewhere safe (password manager). Losing them = losing the
  ability to ever update the app.**

```bash
bubblewrap build
```

Outputs: `app-release-signed.aab` (the store upload) and your key's
**SHA-256 fingerprint** (also printed by
`keytool -list -v -keystore android.keystore`).

## 5. 🧑→🤖 Domain ↔ app handshake

Send Claude the SHA-256 fingerprint (looks like `AB:CD:12:…`). Claude replaces
the placeholder in `serifu/public/.well-known/assetlinks.json` via a PR; once
merged and deployed, verify
`https://YOUR-DOMAIN/.well-known/assetlinks.json` shows your fingerprint.
Without this, the app opens with a browser address bar instead of full-screen.

## 6. 🧑 Play Console listing (~45 min)

1. Console → Create app → name `Serifu`, App (not game), Free.
2. **Internal testing** track first: upload the `.aab`, add your friends'
   Gmail addresses as testers → they get an install link within minutes.
3. Work through the "Set up your app" checklist:
   - Privacy policy URL: `https://YOUR-DOMAIN/privacy.html`
   - App access: everything available without login ✓
   - Ads: none ✓ · Content rating questionnaire: Education/Reference
   - Data safety: no data collected, no data shared (matches privacy.html)
   - Store listing: description + screenshots (ask Claude — generated
     store-ready screenshots and copy on request)
4. When internal testing feels good → Production → submit for review
   (typically 1–7 days).

## Branding reality check

Review goes smoothly for a neutral language-practice tool. Using the Frieren
name/artwork in the store listing without a license risks rejection or
takedown — see RELEASE.md "Going commercial". Keep the listing about the tool;
your first content stays your private use.
