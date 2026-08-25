# Serifu 台詞 — project context

Watch-party Japanese practice: the episode plays in sync for a room of
friends, pauses at your character's line, listens (Web Speech, ja-JP),
scores your attempt 0-100, and auto-resumes on a pass. Learning rides the
loop: furigana scripts, per-line vocab/grammar notes, a wordbook with Anki
CSV export, and a Leitner mastery tracker (習得). Solo memory practice
lives at public per-scene URLs (/#/p/<slug>).

## Architecture (all under serifu/)

- `client/` — React 19 + Vite PWA. Components in `client/src/components/`,
  pure logic in `client/src/lib/` (speech scoring, mastery, wordbook,
  episodes, subtitle parsing), bundled demo content in `client/src/data/`.
- `server/` — Express + Socket.IO room relay (`rooms.ts` holds state +
  validation; in-memory only, no DB). Serves the built client from
  `dist/` (dotfiles allowed — /.well-known must be reachable).
- `shared/types.ts` — the single source of truth for the script format
  (SkitScript → SkitScene chapters → ScriptLine → RubyToken, VocabItem,
  GrammarNote). Server validates everything a client sends against it.
- `e2e/demo.mjs` — two-browser Playwright suite (fake mic + generated
  video); the number in "N/N checks passed" is the contract.

## Commands

```bash
npm run dev          # server :3001 + client :5173
npm run typecheck    # strict, client + server — must stay clean
npm test             # vitest unit suites
npm run build        # production PWA build
npm run e2e          # needs a built app served on :4123 (see CONTRIBUTING.md)
```

## The loop (see CONTRIBUTING.md)

branch → PR → CI green (.github/workflows/ci.yml) → Claude review →
Oscar review → squash merge → Render auto-deploys main. No direct pushes.

## Hard rules

1. **Bring-your-own-media, always.** Never commit episode video/audio,
   full transcripts, OST files, or anime imagery. Bundled scenes are
   short, approximate, original-flavored dialogue only.
2. **Public/commercial surfaces stay anime-agnostic** (store listings,
   marketing copy, paid features). Frieren is the private first use case.
   Details: RELEASE.md "Going commercial", docs/BUSINESS.md.
3. **New logic ships with tests** — pure functions in lib/ or server/,
   plus an E2E check for user-visible behavior.
4. Bilingual UI copy: Japanese-first labels with English support
   (e.g. 「単語帳 / my wordbook」).

## Agent team (.claude/agents/)

Delegate, don't do everything in the main loop: `content-writer` (new
annotated scenes), `growth-marketer` (anime-agnostic copy),
`biz-strategist` (monetization decisions), `release-captain` (PR/CI/
deploy shepherding). Their definitions carry the constraints; keep them
in sync with this file.
