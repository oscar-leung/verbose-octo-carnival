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
   at the start of every claimed line — the actor says it, hits continue
   (or space), and the real delivery plays as instant feedback.
6. **Join voice** to talk it over; pause and replay lines as much as you like.

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

Any Node host with WebSocket support works (Railway, Fly.io, Render, a VPS):

```bash
npm ci && npm run build && npm start   # honors PORT
```

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

## Roadmap ideas (v0.2+)

- Auto-furigana for imported subtitles (kuromoji/kuroshiro).
- Per-line recording + playback: compare your delivery with the original.
- Speech recognition scoring (Web Speech API) for solo practice mode.
- Vocab capture: tap a word in a line → SRS export (Anki/CSV).
- Line loop mode (A-B repeat) and per-character "hide my lines until spoken".
- Persistent script library per room, shareable script gallery.
