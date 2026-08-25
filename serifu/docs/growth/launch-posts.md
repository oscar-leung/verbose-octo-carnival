# Serifu — Launch Posts (ready to paste)

All posts disclose that I'm the builder. No fake accounts, no seeded comments, no
mentioning specific shows. Post from a personal account with history where possible.

---

## 1. r/LearnJapanese (text post)

**Title:** I built a free tool so my friends and I would stop skipping speaking practice — it pauses the show at your character's line until you say it out loud

**Body:**

Like a lot of people here, I could read okay and pass Anki reviews but froze whenever I
actually had to speak. Output practice was the thing I always skipped: italki felt like
a job interview, shadowing alone in my room felt pointless, and I had no one to be bad
at Japanese with.

So I built Serifu (open source, free, no accounts) for my study group. How it works:

- Everyone opens their own copy of an episode of a show; the app keeps playback in sync
- You import the episode's JP subtitles (.srt/.vtt/.ass) and it becomes a timed script
  with furigana and translations
- Each person claims a character. In rehearsal mode, the video pauses at the start of
  your lines — you deliver the line *before* hearing the real actor
- In Chrome/Edge it listens and scores your attempt against the script (kana or kanji
  reading both count); score 70+ and the video auto-resumes. Below that, もう一回！
- Built-in voice chat so you can stop and argue about a grammar point mid-scene

What surprised me: doing this with friends removes the fear almost completely. Botching
a line in front of two friends who are also botching lines is funny, not humiliating —
and you end up repeating lines way more than you would shadowing solo. The scored-pass
mechanic turns 「もう一回」 into a game instead of a chore.

Honest limitations: speech scoring is the browser's recognition (Chrome/Edge; iPhones
use a manual continue button), it's built for 2–6 people, and it ships with only a short
original demo scene — you bring your own episodes and subtitles.

Disclosure: I made this. It's free and there's nothing to buy right now; I'd genuinely
like feedback from people who've tried shadowing before. Happy to answer anything about
how the scoring works.

[link]

---

## 2. r/languagelearning (text post)

**Title:** Speaking practice is the loneliest part of language learning, so I built a watch-party app where you and your friends voice the characters (Japanese, free, I'm the dev)

**Body:**

The pattern I kept seeing in myself and my study group: hundreds of hours of input,
near-zero hours of output, because speaking practice is either expensive (tutors),
terrifying (strangers), or boring (talking to a wall).

My fix was to bolt speaking onto something we already did together: watching shows.
Serifu syncs playback across everyone's own copy of an episode, turns the subtitles you
import into a timed script with readings and translations, and pauses the video whenever
*your* character speaks. You say the line; speech recognition scores it against the
script; pass and the show resumes on its own. Voice chat is built in for the inevitable
"wait, what does that particle do" tangents.

It's Japanese-only for now (furigana handling and kana-aware scoring are the hard parts
I built first), but the shadowing-with-friends model should generalize and I'd love to
hear which language you'd want next.

Disclosure: I'm the developer. Free, open source, no accounts, your video files never
leave your device. Mostly posting because I want to know if this resonates outside my
own friend group — does "output practice with friends via media you love" match anyone
else's experience of what's missing?

[link]

---

## 3. Hacker News — Show HN

**Title:** Show HN: Serifu – synced watch parties where you must voice a character's lines to continue

**First comment (from me, posted immediately):**

Hi HN, builder here. Serifu came out of a personal problem: speaking is the highest-value
and most-avoided part of learning Japanese, because doing it alone is dull and doing it
with strangers is terrifying.

The mechanic: friends each open their own local copy of an episode; the server keeps
playback in sync (server-authoritative {isPlaying, position, updatedAt}, clients
extrapolate and snap on ~0.75s drift). Imported subtitles become a timed script with
furigana. When a line belonging to your claimed character starts, the room pauses; the
Web Speech API scores your spoken attempt via edit-distance after normalization against
both the surface text and the kana reading, and at 70+ playback auto-resumes for everyone.

Technical bits that were fun: WebRTC mesh voice chat with the MDN perfect-negotiation
pattern over Socket.IO signaling; rehearsal pauses detected client-side by whoever
notices the line boundary first, then validated/deduped server-side with a cooldown so
resume doesn't re-trigger; no database — rooms are in-memory and GC'd, and video never
leaves the user's device (only timing + script are shared).

Deliberate constraints: no bundled shows (users import their own subtitles — the app is
content-agnostic by design and by law), Chrome/Edge only for scoring (iOS has no Web
Speech recognition; there's a manual fallback), and it targets 2–6 people, not crowds.

Stack: TypeScript, React, Express + Socket.IO. Open source. Would love scrutiny of the
sync model and thoughts on whether the "speech-gated playback" mechanic has legs beyond
language learning.

---

## 4. X/Twitter thread (6 tweets)

**1/** Speaking practice is the part of learning Japanese everyone skips. Not because it
doesn't work — because doing it alone is boring and doing it with strangers is
terrifying. So my friends and I stopped practicing speaking… and built a workaround.

**2/** The idea: we already watched shows together. What if the show *refused to
continue* until you said your character's line out loud?

**3/** That's Serifu. Everyone opens their own copy of an episode, playback stays
perfectly in sync, and a furigana script scrolls alongside. Claim a character → the
video pauses at your lines → you deliver them before the real actor does.

**4/** The magic moment: it listens. Say your line, get scored 0–100 against the script
(kanji or kana). Hit 70+ and the show auto-resumes for the whole room. Miss, and your
friends hear the attempt on voice chat. Terrifying alone. Hilarious together.

**5/** Honest bits: I built it (free, open source, no accounts). You bring your own
episodes + subtitles — nothing is streamed or uploaded, video never leaves your device.
Speech scoring needs Chrome/Edge; everyone else gets a manual continue button.

**6/** If you've ever paused a show to whisper a line back at the screen — this is that,
turned into a game you play with friends. Grab 2 friends and an episode: [link]
