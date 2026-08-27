# Contributing / the vibe-coding loop

This project runs on a simple, strict loop — human ideas, AI hands, both sets
of eyes on every change:

```
idea → branch → PR → CI green → Claude reviews → Oscar reviews → squash merge → Render auto-deploys main
```

## The rules

1. **No direct pushes to `main`.** Every change is a PR, even one-liners.
2. **CI must be green before merge.** The pipeline (`.github/workflows/ci.yml`)
   runs on every PR: strict typecheck (client + server), all unit tests, the
   production PWA build, and the full two-browser E2E demo (join, sync, speech
   scoring, mastery, scenes, episodes) against the built app. E2E screenshots
   are attached to each run as artifacts.
3. **Two reviews.** Claude reviews first (subscribe the session to the PR, or
   ask for a review pass); Oscar has the final word and clicks merge.
   Squash-merge with a `feat(serifu): …` title so `main` stays readable.
4. **Deploys are boring.** Merging to `main` is the deploy — Render picks it
   up automatically. Verify `/healthz` and click around after each merge.
5. **New logic ships with tests.** Pure logic goes in `lib/` or `server/` as
   testable functions; UI behavior gets an E2E check in `e2e/demo.mjs`.

## Recommended repo settings (one-time, in GitHub → Settings → Branches)

Add a branch protection rule for `main`:
- Require a pull request before merging (1 approval)
- Require status checks to pass: **CI / typecheck · unit · build · e2e**
- Require branches to be up to date before merging

## Local commands

```bash
cd serifu
npm run dev        # server :3001 + web :5173
npm run typecheck && npm test
npm run build && PORT=4123 npm start   # then, in another shell:
npm run e2e        # full browser suite (CHROMIUM_PATH=… if needed)
```

## Style

- Match the existing code: strict TS, no new dependencies without a reason,
  bilingual UI copy (Japanese-first labels, English support).
- Content stays bring-your-own-media: never commit episode transcripts,
  video, audio, or anime imagery. Bundled demo content is short, approximate,
  and original-art only. See RELEASE.md ("Going commercial") before anything
  user-facing changes branding.
