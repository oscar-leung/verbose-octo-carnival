# Serifu 台詞

Practice Japanese by **voicing your favorite anime scenes with friends**.

Everyone joins a room, opens their own copy of an episode, and the app keeps
playback in sync. A timed script scrolls alongside the video with furigana and
English translations. Each person claims a character — and in **rehearsal
mode** the video auto-pauses right when your line starts, so *you* deliver it
before hearing the real voice actor. Built-in voice chat lets you pause
anytime to talk about a phrase (or about how good Himmel looks).

Built for small groups of friends studying together — no accounts, no
database, nothing uploaded. Video files never leave your device; only timing
and the script are shared.

## Quick start

```bash
cd serifu
npm install
npm run dev        # server on :3001, web app on http://localhost:5173
```

Open http://localhost:5173, enter a name, create a room, and send the link to
a friend (or open it in a second tab to see the sync).

Other commands:

```bash
npm test           # unit tests (subtitle parser, room state machine)
npm run typecheck  # strict TS across client + server
npm run build      # build the client into dist/
npm start          # production: one server serving dist/ + websockets
npm run e2e        # full browser demo test (needs a running server: PORT=4123 npm start)
```

The e2e script drives two headless Chromium users through the whole story —
create room, join by link, load demo script, claim characters, load a
generated video, synced play, rehearsal auto-pause + resume, voice chat with
a real WebRTC connection, mute propagation, editor, click-to-seek — and drops
screenshots in `e2e/shots/`. Point it at a Chromium binary with
`CHROMIUM_PATH=/path/to/chrome` if Playwright's default lookup fails.

## How a session works

1. **Create a room** and share the link.
2. **Everyone opens the same episode** as a local video file (📁 button).
   Different encodes drift? Use *my offset* in the top right of the script
   column to nudge your local video against the room timeline.
3. **Load a script**: the bundled demo scene, or import the episode's `.srt` /
   `.vtt` subtitles in the 台本 editor, tag each line with its speaker, and
   apply. Timings off? The editor's *shift all* tool moves every line at once.
4. **Claim your characters** in the 配役 bar.
5. Press play. With **セリフで自動停止 (rehearsal mode)** on, the video pauses
   at the start of every claimed line. In Chrome/Edge the app then **listens**:
   say your line, it's scored live against the script (kanji or kana reading,
   0–100), and at **70+ the anime auto-resumes** — no clicking. Below that you
   see your score and what it heard (もう一回！); everyone in the room watches
   your attempts land in real time. No speech support? The continue button
   (or space) always works.
6. **Join voice** to talk it over; pause and replay lines as much as you like.
7. Prep episodes one at a time in the editor and **save them to your episode
   library** (エピソード書庫) — import ep. 2's subtitles next week, load ep. 1
   back with one click.

## Getting real episode subtitles

The importer accepts `.srt`, `.vtt`, and `.ass/.ssa` (the format most Japanese
subtitle archives use — ASS speaker names, when present, are auto-converted
into characters with lines pre-assigned).

- **[jimaku.cc](https://jimaku.cc/)** — dedicated Japanese-subtitle archive.
  Frieren: [Season 1 (entry 729)](https://jimaku.cc/entry/729) and
  [Season 2 (entry 11446)](https://jimaku.cc/entry/11446) have JP subs for
  every episode. Free account; there's also an API (25 req/min) if we later
  automate per-episode fetching.
- **kitsunekko** — the older mirror many of jimaku's files came from.

Workflow per episode: download the episode's JP subtitle file → 台本 editor →
import → tag/verify speakers → *shift all* until line 1 matches your video →
**save to エピソード書庫** → export JSON to share with friends. ~15 minutes per
episode, once.

## Voice chat behind strict NATs (optional TURN)

Voice uses STUN by default, which covers most home networks. If two friends
can't hear each other (symmetric NAT, campus/corporate Wi-Fi), give the server
TURN credentials via environment variables — no code change needed; clients
fetch them from `/api/ice`:

```
TURN_URLS=turn:your.relay:80,turn:your.relay:443?transport=tcp
TURN_USERNAME=...
TURN_CREDENTIAL=...
```

A [free metered.ca account](https://www.metered.ca/tools/openrelay/) includes
20 GB/month of TURN relay — paste its credentials into Render's environment
settings.

## Script format

Scripts are JSON (`export JSON` in the editor produces this shape):

```jsonc
{
  "title": "第1話 — 流星群の約束",
  "characters": [{ "id": "frieren", "name": "フリーレン", "color": "#7ecbff" }],
  "lines": [
    {
      "id": "l1",
      "character": "frieren",
      "start": 14.5,
      "end": 18.5,
      "tokens": [
        { "t": "たった" },
        { "t": "十年", "r": "じゅうねん" },
        { "t": "だよ。" }
      ],
      "translation": "It was only ten years."
    }
  ]
}
```

In the editor you write furigana inline with Aozora-style notation:
`十年《じゅうねん》` attaches the reading to the kanji run before it, and
`｜今日《きょう》` marks the base explicitly.

## Architecture

```
serifu/
├─ shared/types.ts        # domain + socket protocol types (client & server)
├─ server/
│  ├─ index.ts            # Express + Socket.IO; serves dist/ in production
│  └─ rooms.ts            # in-memory room state machine (tested)
└─ client/src/
   ├─ lib/                # useRoom hook, playback math, SRT/ruby parser,
   │                      # WebRTC mesh (perfect negotiation), settings
   ├─ components/         # Room, VideoPanel, ScriptPanel, ScriptEditor,
   │                      # CharacterBar, VoicePanel, RehearsalBanner…
   └─ data/demoScript.ts  # bundled demo scene
```

Design notes:

- **Playback sync** is server-authoritative: the server stores
  `{isPlaying, position, updatedAt}` stamped with its own clock; clients
  extrapolate and snap their `<video>` when drift exceeds ~0.75 s. Any client
  may control playback — it's a living-room remote, not a host model.
- **Rehearsal pauses** are detected client-side (whoever notices the line
  crossing first reports it) and validated server-side: claimed lines only,
  deduped, position-checked, with a cooldown so resuming doesn't re-trigger.
- **Voice chat** is a full WebRTC mesh (fine for ~2–6 people) using the MDN
  perfect-negotiation pattern over Socket.IO signaling, STUN only.
- **No persistence**: rooms live in memory and are garbage-collected ~30 min
  after emptying. Export your script JSON to keep it.

## Deploying for your friends

Ready-made configs are included:

- **Render (recommended, free)**: `render.yaml` at the repo root is a Blueprint.
  On render.com: *New + → Blueprint → connect the GitHub repo → Apply*. Done —
  you get `https://serifu-….onrender.com`. The free instance sleeps when idle;
  the first visit after a break takes ~30–60 s to wake.
- **Fly.io / Railway / any Docker host**: `serifu/Dockerfile` (+ `fly.toml`).
- **Bare Node host**: `npm ci && npm run build && npm start` (honors `PORT`).

Two caveats:

- **HTTPS is required** for mic access (WebRTC) on non-localhost origins —
  the platforms above give you TLS automatically.
- Voice uses **STUN only**; a strict NAT pair may fail to connect. If that
  bites, add a TURN server to `ICE_SERVERS` in `client/src/lib/voice.ts`
  (e.g. a free Metered/Twilio TURN credential) — or just use Discord for
  audio and Serifu for everything else.

## A note on content

Serifu ships with a short, approximate demo scene only. For real episodes,
import subtitles you own/ripped yourself and keep rooms among friends —
distributing full copyrighted transcripts or video is on you to avoid.

## Speech scoring notes

- Uses the browser's Web Speech API (`ja-JP`) — Chrome and Edge only; Firefox
  and most iOS browsers fall back to the manual continue button.
- Scoring is edit-distance similarity after normalization (katakana→hiragana,
  punctuation stripped), taken against both the surface text and the furigana
  reading, so 「おうとは…」 and 「王都は…」 both count.
- Pass threshold is `PASS_SCORE` (70) in `client/src/lib/speech.ts`.

## Roadmap ideas (v0.3+)

- Auto-furigana for imported subtitles (kuromoji/kuroshiro).
- Per-line recording + playback: compare your delivery with the original.
- Vocab capture: tap a word in a line → SRS export (Anki/CSV).
- Line loop mode (A-B repeat) and per-character "hide my lines until spoken".
- Shareable episode gallery (server-side script library) for the full
  S1+S2 release.
