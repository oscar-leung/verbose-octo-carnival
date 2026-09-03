# Serifu design audit 02 — modals, editor, matured phone layout

Date: 2026-09-03 · Auditor: ux-designer · Build: production (`npm run build`, served on :4700)
Screens: landing (+もっと見る), room all three phone tabs with 名場面集 loaded, script editor
(desktop), solo fresh / 暗記 / completion, wordbook·mastery·episodes modals on phone.
Viewports: 1440x900 and 390x844. Evidence: PNGs in this directory.

**Regression check on audit-01:** all 9 findings verified shipped and working — landing fits one
phone viewport with 3 chips + もっと見る (`07`), stage tab is one-line copy + 台本へ link (`10`),
room settings live in その他 with EN sublabels (`11`), solo nav/footer/segments are in place
(`15`). Horizontal scroll at 390px: **0px overflow on every screen tested — pass.**

Severity: **blocker** · **friction** · **polish**. **[CSS-only]** = ready-to-apply snippet for
`client/src/styles.css`. No blockers this round; the top of the list is the new modal-ergonomics
standard.

---

## 1. Phone modals are centered popovers, not sheets — ✕ out of thumb reach, no bottom anchor

**Severity: friction** · Evidence: `12-modal-wordbook-390.png`, `13-modal-mastery-390.png`,
`14-modal-episodes-390.png`

At 390px all four modals (`.modal` in Wordbook / MasteryPanel / EpisodeBrowser / ScriptEditor)
float mid-screen over a visibly cluttered backdrop. The only labeled close control is a ~44px ✕
chip at the **top-right** — the farthest point from the thumb. Backdrop-tap-to-close exists in
code but has zero affordance. Small modals (wordbook, mastery) hover awkwardly with the その他
tab bleeding through above *and* below.

**Change [CSS-only]** — make every modal a bottom sheet on phones; one rule covers all four:

```css
@media (max-width: 720px) {
  .modal-backdrop {
    align-items: flex-end;
    padding: 0;
  }
  .modal {
    width: 100%;
    max-height: 88dvh;
    border-radius: 16px 16px 0 0;
    border-bottom: none;
    padding-bottom: calc(16px + env(safe-area-inset-bottom));
  }
  /* sheet affordance: a grab handle where the thumb expects one */
  .modal::before {
    content: '';
    align-self: center;
    width: 36px;
    height: 4px;
    border-radius: 2px;
    background: var(--border);
    flex-shrink: 0;
  }
}
```

Bottom-anchored, the ✕ stays as-is for reachability-by-convention, and backdrop dismissal
becomes the natural "swipe-away" spot above the sheet. No component changes required.

---

## 2. 話数 episodes modal at 390px: colliding header, 5-line English essay, 28 truncated rows

**Severity: friction** · Evidence: `14-modal-episodes-390.png`

Three problems stack: (a) the `h2` "話数 / episodes (0 prepped · 0 practiced)" wraps to two
lines and runs under the ✕ chip; (b) a five-line English paragraph (README → jimaku.cc …)
precedes any content — Oscar's directive: less text; (c) every one of 28 slots shows the same
truncated placeholder `episode title (yo` + 未準備 + ✎, so the screen reads as a wall of broken
inputs rather than "a journey at a glance".

**Change:** `client/src/components/EpisodeBrowser.tsx`
- Header: `話数 / episodes` only; move `({prepped} prepped · {practiced} practiced)` to its own
  12.5px muted line under the header (it currently lives inside the `h2` `<small>`, ~line 46).
- `episodes-hint` (~line 52): cut to one line —
  `字幕を取り込んで各話を準備してね — import an episode's subs to prep it (README → jimaku.cc).`
- `ep-title` input placeholder: `episode title (your own note)` → `タイトル / title` — it then
  fits at 390px and follows the bilingual rule.
- Collapse Season 2 behind its `season-label` (accordion, default closed) until at least one of
  its episodes is prepped — first-time users see 12 rows, not 28.

---

## 3. Script editor tools are one flat pile — the real prep flow has an order the UI hides

**Severity: friction** · Evidence: `04-editor-top-1440.png`

The real episode-prep flow is: **import subs → assign 話者 → auto-furigana → translate →
chapter 名場面 → save to library → apply**. The tools row instead interleaves eight unrelated
controls (title, demo select, import, paste, furigana, shift-all, export) in one wrapped line,
with the library on a second line and 配役 third. A first-time prepper cannot tell where to
start; auto-furigana — the star of this round — is visually a peer of "shift all".

**Change:** `client/src/components/ScriptEditor.tsx` — regroup `.editor-tools` +
`.editor-library` into three labeled rows using the existing `.bar-label` style, in flow order:
1. `① 取り込み / import` — import file · paste subtitles · load demo scene
2. `② 注釈 / annotate` — ふりがな自動付与 (promote to `class="primary"`) · shift all
3. `③ 保存 / save` — エピソード書庫 select/load/save · export JSON · title input

Copy stays identical; this is layout + one class. Keep the footer as-is (`apply to room` is
already correctly the single primary at bottom-right).

---

## 4. Editor line inputs truncate the two things you edit most

**Severity: friction** · Evidence: `04-editor-top-1440.png` (lines 2, 4, 7 cut mid-sentence;
every translation clipped at ~24 chars)

Even at 1440px, `grid-template-columns: … minmax(200px, 2fr) minmax(140px, 1.2fr) …` clips
Japanese with ruby markup (`十年間《じゅうねんかん》の冒険…` ends mid-token) and nearly every
English translation. For a 300-line episode this means editing blind inside single-line
scrollable inputs — the core annotation surface.

**Change [CSS-only]** — give JP text the full row and drop translation to a second row on all
widths (the ≤1000px block already does exactly this; promote the pattern):

```css
.editor-line {
  grid-template-columns: 28px 130px 70px 70px minmax(300px, 1fr) 30px 30px;
}
.editor-line .translation-input {
  grid-column: 2 / -1;
}
```

(Line height doubles; `.editor-lines` already scrolls internally, and the timestamp/speaker
columns stay aligned. Delete the now-redundant overrides in the `@media (max-width: 1000px)`
block.)

---

## 5. Solo 暗記 mode shows the answers under the question

**Severity: friction** · Evidence: `16-solo-anki-390.png`

At 暗記 the line masks to `＿＿＿…` and the EN translation correctly becomes the prompt — but
directly beneath, the LearnPanel still shows the vocab chips **with readings and meanings**
(王都/おうと/royal capital…) and full grammar bullets. The recall moment — this page's one job —
is answered by its own footnotes. It also pushes `.solo-nav` a full screen down.

**Change:** `client/src/components/SoloPractice.tsx` (~line 243) — when `hideLevel >= 2`,
collapse `<LearnPanel>` behind a single quiet disclosure chip: `📖 ノートを見る / peek notes`
(tap to expand, auto-collapses on line advance). Level 0–1 keeps the panel open as today.
This pairs with the existing 👁 チラ見 button — one peeks the line, one peeks the notes.

---

## 6. Solo header truncates the scene title — again, from the other side

**Severity: polish** · Evidence: `15-solo-fresh-390.png`, `17-solo-done-390.png`

Audit-01 stripped the series prefix, but at 390px the title still renders `第1話 — 流星...`:
`.solo-title` is `white-space: nowrap` squeezed between two full-width chips (`← Serifu`,
`share ⧉`). The scene identity never survives.

**Change [CSS-only]:**

```css
@media (max-width: 720px) {
  .solo-header .chip {
    padding: 8px 10px;
    font-size: 13px;
  }
  .solo-title {
    white-space: normal;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    font-size: 15px;
    line-height: 1.3;
  }
}
```

Optionally shorten chip copy in `SoloPractice.tsx`: `← Serifu` → `←`, `share ⧉` → `⧉`
(keep `aria-label`s); with icons-only chips the title rarely needs the second line.

---

## 7. 名場面 chapter bar eats a third of the 台本 tab before the first line

**Severity: polish** · Evidence: `09-room-script-390.png`

On the script tab the wrapped scene-chip bar (名場面 + 3 chips over two rows) plus the room
header consume ~330px before any dialogue appears. Chapters are a jump control, not content.

**Change [CSS-only]** — one-row horizontal snap scroll on phones:

```css
@media (max-width: 720px) {
  .scene-bar {
    flex-wrap: nowrap;
    overflow-x: auto;
    scroll-snap-type: x proximity;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .scene-bar .chip.scene {
    flex-shrink: 0;
    scroll-snap-align: start;
  }
}
```

---

## 8. Completion screen brags about "0 attempts"

**Severity: polish** · Evidence: `17-solo-done-390.png`

Skipping lines with ✓ (no mic, the documented fallback) ends in `12 lines in 0 attempts.` —
nonsense arithmetic at the emotional peak of the loop, followed by a two-line English
explanation of the mastery tracker.

**Change:** `client/src/components/SoloPractice.tsx` `.solo-done` (~line 155) — when
`attempts === 0`: `12 lines spoken — 習得に記録したよ.` When `attempts > 0`:
`{passed} lines · {attempts} attempts — 習得に記録したよ.` Drop the rest of the paragraph;
the 習得 tracker explains itself when opened.

---

## 9. Motion: the `pulse` animation ignores prefers-reduced-motion

**Severity: polish** · Evidence: code — `styles.css` lines 276, 468 (`animation: pulse … infinite`)

`NightSky.tsx` respects reduced motion, but `.conn-dot.off` and `.mic-live` pulse forever with
no guard — and `.mic-live` runs precisely during the speaking moment. Grep confirms zero
`prefers-reduced-motion` rules in `styles.css`.

**Change [CSS-only]:**

```css
@media (prefers-reduced-motion: reduce) {
  .conn-dot.off,
  .mic-live {
    animation: none;
  }
  .solo-bar i {
    transition: none;
  }
}
```

---

## Summary for frontend-dev

| # | Severity | Component | CSS-only |
|---|----------|-----------|----------|
| 1 | friction | styles.css (all modals)            | yes |
| 2 | friction | EpisodeBrowser.tsx                 | no  |
| 3 | friction | ScriptEditor.tsx                   | no  |
| 4 | friction | styles.css (editor lines)          | yes |
| 5 | friction | SoloPractice.tsx / LearnPanel      | no  |
| 6 | polish   | styles.css (+opt. SoloPractice)    | yes |
| 7 | polish   | styles.css                         | yes |
| 8 | polish   | SoloPractice.tsx                   | no  |
| 9 | polish   | styles.css                         | yes |

Suggested order: 1 (unblocks the modal standard for everything else) → 2 → 5 → 4 → 3 → 6-9.
Not screenshot: RestorePrompt (needs a server-restart rig) — code review only: copy and 42px+
buttons look right; fold it into the next audit's e2e-rigged pause-moment pass along with
RehearsalBanner.
