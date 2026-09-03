# Play Store screenshots — capture notes

Captured 2026-09-03 from the real app (production build served locally),
Chromium at 412x732 CSS px, deviceScaleFactor 2 → **824x1464 PNG (9:16)**.

Why not the taller 824x1830: Google Play rejects screenshots whose longer
side exceeds **2x** the shorter side (accepted range 320–3840 px per side,
aspect between 16:9 and 9:16). 824x1830 is 2.22:1 and would not upload;
824x1464 is exactly 9:16.

All room shots use an **original, anime-agnostic scene** — 「夏祭りの夜
(オリジナルデモ)」, three original characters (アオイ・レン・ユキ), written for
these screenshots and loaded through the script editor's paste-import (it
is not part of the app bundle). The "episode" behind the script is a
generated night-festival placeholder clip (canvas render: stars, moon,
lanterns, fireworks) — no show footage anywhere.

## File → listing caption (docs/growth/store-listing.md shot list)

| File | Shot list # | Caption (overlay to be added in a design pass) |
| --- | --- | --- |
| `01-hero-your-line.png` | 1 — Hero | "Your line. Say it out loud." |
| `02-score-pass.png` | 2 — Payoff | "Nail it and the show rolls on — automatically." |
| `03-together-sync.png` | 3 — Together | "Perfectly synced with friends, anywhere." |
| `04-script-furigana.png` | 4 — The script | "Furigana + translations for every line." |
| `05-import-editor.png` | 5 — Bring any show | "Import subtitles from any show you own." |
| `06-solo-practice.png` | 6 — Keep what you learn | "Drill your lines and vocab between sessions." |
| `07-mastery-review.png` | spare / alt for 6 | Spaced-repetition review card (習得) fed by spoken passes. |
| `08-episode-browser.png` | spare | Season/episode tracker — prep an episode once, reload any week. |
| `09-landing.png` | spare | Landing: no accounts, videos stay on device. |

Play allows up to 8 phone screenshots; upload 01–06 plus any two of 07–09.

## Substitutions and deviations from the shot list

- **Shot 2**: the spec mocked "84/100"; the real capture shows the genuine
  scoring pipeline passing at **86%** (「🎉 86% — 合格！ rolling…」). Honest > staged.
- **Shot 3**: on the phone layout the voice-chat panel lives on the その他
  tab, not the stage, so this frame shows the synced stage + the claimed
  three-person cast (アオイ/あなた, レン/Yui, ユキ/Ren) instead of a voice
  panel + avatars split. The voice panel is visible in `07-mastery-review.png`'s
  background. A desktop/tablet capture would show both at once if shot 3
  needs strengthening.
- **Shot 6**: solo-practice pages only exist for the bundled demo scenes,
  whose speaker labels are licensed character names. The scene chosen
  (花畑の魔法) has a neutral displayed title and the visible line/translation
  contain no names; the speaker-name label was **blurred at capture time**.
- `09-landing.png`: the third solo-scene chip contains a licensed character
  name and was **blurred at capture time**; the other visible chips are
  name-free.
- Rehearsal shots (1, 2) were driven by a scripted SpeechRecognition stub —
  same UI path a real mic exercises.
- No caption overlays are baked in; captions above should be composited in
  a device-frame/branding pass before upload.

## Before submitting — retake checklist

1. The two blurred frames (06, 09) should ideally be **retaken after the
   bundled demo content is swapped for neutral scenes** (or the blur
   accepted as-is; Play permits it, but crisp frames sell better).
2. Room shots are already IP-clean and can ship as-is, but retake against
   the live domain (not localhost — the room-code chip is the only tell,
   it shows a random code either way) if pixel-perfect parity is wanted.
3. Re-verify current Play asset specs at upload time:
   https://support.google.com/googleplay/android-developer/answer/9866151

## Reproduction

`tools/capture.mjs` (+ `tools/script.json`, the original scene) drives the
UI end-to-end with Playwright: creates the room, paste-imports the scene
JSON, joins two extra users, claims characters, plays into the rehearsal
auto-pause, and fakes the spoken attempts. Rerun against any build:

```bash
npm run build && PORT=4600 npm start   # in serifu/
BASE=http://localhost:4600 node docs/store-assets/play/tools/capture.mjs
```

(Uses the playwright-core already in serifu/node_modules; edit the
hardcoded Chromium `executablePath` for your machine.)
