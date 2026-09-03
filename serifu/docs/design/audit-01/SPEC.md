# Serifu design audit 01 — first full pass

Date: 2026-09-03 · Auditor: ux-designer · Build: production (`npm run build`, served on :4123)
Screens: landing, empty room, room with 名場面集 loaded, solo practice (`/#/p/meteor-promise`), at 1440x900 and 390x844.
Evidence: PNGs in this directory. Horizontal scroll check at 390px: **0px overflow everywhere — pass.**

Scope note: the rehearsal pause banner itself (RehearsalBanner during playback) needs media + a
claimed role and was not screenshot in this pass; findings 2 and 5 still touch it via shared
settings. A follow-up audit should capture the pause moment with the e2e fake-video rig.

Severity: **blocker** (breaks or hides core value) · **friction** (slows/confuses a first-timer) · **polish**.
Findings marked **[CSS-only]** are ready-to-apply snippets for `client/src/styles.css`.

---

## 1. Translation blur reads as broken rendering on phones — "on hover" has no hover

**Severity: blocker** · Evidence: `03-scene-script-390.png`, `03-scene-loaded-1440.png`

The default 訳 setting is "on hover", so every English line in the script panel (and the
rehearsal banner, which shares `hover-reveal`) is blurred. On a 390px phone there is no
hover: the first-time user sees twelve smeared grey lines and no affordance that a tap
reveals anything — it looks like a font-rendering bug, and it sits directly under the line
being rehearsed.

**Change:**
- `client/src/styles.css` — make the reveal work for touch and keyboard **[CSS-only]**:
  ```css
  .hover-reveal:hover,
  .hover-reveal:active,
  .hover-reveal:focus-visible {
    filter: none;
  }
  ```
- `client/src/components/Room.tsx` (settings-row `select`, ~line 275): rename the option
  copy `on hover` → `タップ / tap`, so the label matches the actual gesture and the
  bilingual rule. `show` → `表示 / show`, `hide` → `隠す / hide`.

---

## 2. Solo practice: the primary action drifts out of thumb reach

**Severity: friction** · Evidence: `04-solo-390.png`, `04-solo-hint-390.png`

`✓ said it — next` / `skip →` sit *below* the vocab chips and grammar notes, ~680px down,
and their position shifts with every line's note length (compare the two screenshots — the
buttons jump ~50px between hide levels). This is the button the learner presses after
every single line; it should be anchored where the thumb already is.

**Change:** `client/src/components/SoloPractice.tsx` — `.solo-nav` becomes a sticky footer
of the card. **[CSS-only]**:
```css
@media (max-width: 720px) {
  .solo-nav {
    position: sticky;
    bottom: 0;
    background: rgba(22, 26, 34, 0.97);
    border-top: 1px solid var(--border);
    margin: 0 -16px -16px; /* match .solo-card padding */
    padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
    z-index: 5;
  }
}
```
Also move the 判定 threshold `select` out of `.solo-nav` (it is a set-once setting, not a
per-line control) — tuck it next to the hide-level chips or behind the header.

---

## 3. Empty-room stage opens on a four-line English essay

**Severity: friction** · Evidence: `02-room-empty-stage-390.png`, `02-room-empty-stage-1440.png`

The very first screen after "Create a room" is a JP heading plus a 4-line English paragraph
explaining sync semantics, before the one button that matters. Oscar's standing directive:
less text. The screen's one job is "open your file (or go load a script)".

**Change:** `client/src/components/VideoPanel.tsx` (empty state) — keep the JP heading
`みんなそれぞれ、自分の動画ファイルを開いてね`, cut the paragraph to one line:
`Nothing uploads — playback just stays in sync.` Drop the "No file? …" sentence; instead,
on mobile, add a quiet link under the button: `動画なしでもOK — 台本へ →` that switches to
the 台本 tab (setMobileTab('script')).

---

## 4. その他 tab and desktop header tools are Japanese-only — bilingual rule broken

**Severity: friction** · Evidence: `02-room-empty-more-390.png`, `02-room-empty-stage-1440.png`

話数 / 習得 / 単語帳 / 台本 ✎ carry no English support anywhere. The design system is
Japanese-first *with English support* (CLAUDE.md rule 4); a beginner — the actual target
user — cannot decode which of these is the wordbook. The その他 tab is these buttons' only
home on the primary surface.

**Change:** `client/src/components/Room.tsx` `.more-actions` (~line 242) and the desktop
header buttons — add a small EN sublabel inside each button, matching the `.mnav-btn`
pattern: `話数 <small>episodes</small>`, `習得 <small>mastery</small>`,
`単語帳 <small>wordbook</small>`, `台本 ✎ <small>edit script</small>`. Style `small` at
11px `var(--muted)`, block on mobile / inline on desktop.

---

## 5. Stage tab carries settings that compete with the performance moment

**Severity: friction** · Evidence: `03-scene-stage-390.png`

With a scene loaded, the 390px stage stacks: role-claim chips (correct — that IS the job),
plus `セリフで自動停止` checkbox and the `判定 ふつう70+` select. Those two are room-level,
set-once host settings; during rehearsal they are clutter directly under the video, and the
checkbox's tap target is the 14px box itself.

**Change:** `client/src/components/CharacterBar.tsx` — on mobile, keep only the claim
chips on the stage tab; render the auto-pause toggle and 判定 select in the その他 tab
(alongside ふりがな/訳 in `.settings-row`, Room.tsx). Desktop can keep them in the bar.

---

## 6. Landing at 390px: three jobs and six demo chips on one screen

**Severity: friction** · Evidence: `01-landing-390.png`, `01-landing-1440.png`

Create, Join, and six solo-practice chips — each chip repeating `(デモ)` — fill the phone
viewport and push the trust line ("No accounts…") off-screen. `(デモ)` six times is pure
noise; the chip list is a second product (solo practice) crowding the first (rooms).

**Change:** `client/src/components/Landing.tsx`:
- Drop `(デモ)` from each chip; say it once in the section label:
  `一人で練習 — solo practice (デモ台本):`
- Show 3 chips + `もっと見る / more…` (expands), or make the list horizontally
  snap-scrolling one-row. Either keeps Create/Join + trust line in the first viewport.

---

## 7. Solo hide-level chips wrap into a ragged two-row cluster

**Severity: polish** · Evidence: `04-solo-390.png` (暗記 orphaned on row 2)

The four levels (全部見る → ふりがな無し → ヒント → 暗記) are a linear progression — the
core interaction of the page — but render as wrapped pills, with 暗記 orphaned. A one-row
segmented control communicates "difficulty slider" and frees a row.

**Change:** **[CSS-only]** in `client/src/styles.css`:
```css
@media (max-width: 720px) {
  .hide-levels {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
  }
  .hide-levels .chip {
    padding: 8px 4px;
    font-size: 13px;
    text-align: center;
    justify-content: center;
  }
}
```
(13px is acceptable here: these are control labels, not body text.)

---

## 8. Solo footer paragraph is marketing copy inside a practice loop

**Severity: polish** · Evidence: `04-solo-390.png`, `04-solo-1440.png`

"Solo memory practice — for the full experience (synced episode video, friends, voice
chat, rehearsal auto-pause), create a room." — 20 words of feature list on every line of
every practice session. Less text.

**Change:** `client/src/components/SoloPractice.tsx` `.solo-footer` (~line 256) — one
line: `友達と一緒に観るなら → create a room`. Nothing else.

---

## 9. Solo mobile header truncates to the series name, not the scene

**Severity: polish** · Evidence: `04-solo-390.png` (`葬送のフリーレ...`)

At 390px the `h1.solo-title` shows only the series prefix — the one part of the title that
is identical across every scene — and truncates the part that identifies *this* scene.

**Change:** `client/src/components/SoloPractice.tsx` (~line 134) — strip the series prefix
the way `ScriptPanel.tsx` line 78 already does
(`.replace('葬送のフリーレン — ', '').replace('葬送のフリーレン ', '')`), showing e.g.
`第1話 — 流星群の約束 (デモ)`.

---

## Summary for frontend-dev

| # | Severity | Component | CSS-only |
|---|----------|-----------|----------|
| 1 | blocker  | styles.css + Room.tsx | partial |
| 2 | friction | SoloPractice.tsx / styles.css | yes (sticky nav) |
| 3 | friction | VideoPanel.tsx | no |
| 4 | friction | Room.tsx | no |
| 5 | friction | CharacterBar.tsx + Room.tsx | no |
| 6 | friction | Landing.tsx | no |
| 7 | polish   | styles.css | yes |
| 8 | polish   | SoloPractice.tsx | no |
| 9 | polish   | SoloPractice.tsx | no |

Suggested order: 1 → 2 → 3/4 (copy passes together) → 5 → 6 → 7-9.
Motion: no new animation is introduced by any change; the `.hover-reveal` transition
already exists — wrap any new transitions in `@media (prefers-reduced-motion: no-preference)`.
