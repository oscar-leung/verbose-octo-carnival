import { useEffect, useMemo, useRef, useState } from 'react';
import type { RubyToken, ScriptLine, SkitScript } from '../../../shared/types';
import { PASS_SCORE, scoreAttempt, SpeechListener, speechSupported } from '../lib/speech';
import { recordExposure } from '../lib/mastery';
import { loadSettings } from '../lib/settings';
import NightSky from './NightSky';
import RubyText from './RubyText';
import LearnPanel from './LearnPanel';
import GrammarIndex from './GrammarIndex';

interface Props {
  slug: string;
  script: SkitScript;
}

/**
 * Public solo memory practice — one shareable URL per scene, in the spirit of
 * audio-memory sites: read a line, progressively hide it (full → no furigana
 * → first-character hints → full 暗記), then say it from memory. A passing
 * spoken attempt advances to the next line and feeds the mastery ledger.
 */

const HIDE_LEVELS = ['全部見る', 'ふりがな無し', 'ヒント', '暗記'] as const;

/** Mask a line's tokens for the given hide level. */
export function maskTokens(tokens: RubyToken[], level: number): RubyToken[] {
  if (level <= 0) return tokens;
  return tokens.map((tok) => {
    const chars = [...tok.t];
    let text = tok.t;
    if (level === 2) text = chars.map((c, i) => (i === 0 ? c : '＿')).join('');
    if (level >= 3) text = chars.map(() => '＿').join('');
    return { t: text };
  });
}

export default function SoloPractice({ slug, script }: Props) {
  const lines = script.lines;
  const [index, setIndex] = useState(0);
  const [hideLevel, setHideLevel] = useState(0);
  const [peek, setPeek] = useState(false);
  const [threshold, setThreshold] = useState(PASS_SCORE);
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState('');
  const [lastScore, setLastScore] = useState<number | null>(null);
  const [lastHeard, setLastHeard] = useState('');
  const [passedLines, setPassedLines] = useState<Set<string>>(new Set());
  const [attempts, setAttempts] = useState(0);
  const [copied, setCopied] = useState(false);
  const [grammarOpen, setGrammarOpen] = useState(false);
  const settings = useMemo(loadSettings, []);
  const listenerRef = useRef<SpeechListener | null>(null);
  const advancedRef = useRef(false);
  const thresholdRef = useRef(threshold);
  thresholdRef.current = threshold;

  const line: ScriptLine | undefined = lines[index];
  const char = line ? script.characters.find((c) => c.id === line.character) : undefined;
  const done = passedLines.size >= lines.length;

  // Listen while a line is active; a pass advances automatically.
  useEffect(() => {
    advancedRef.current = false;
    setInterim('');
    setLastScore(null);
    setLastHeard('');
    if (!line || done || !speechSupported()) {
      setListening(false);
      return;
    }
    const current = line;
    const listener = new SpeechListener();
    listenerRef.current = listener;
    const ok = listener.start({
      onInterim: setInterim,
      onFinal: (text) => {
        if (advancedRef.current) return;
        const score = scoreAttempt(text, current);
        setAttempts((n) => n + 1);
        setInterim('');
        setLastScore(score);
        setLastHeard(text);
        if (score >= thresholdRef.current) {
          advancedRef.current = true;
          listener.stop();
          recordExposure([
            ...(current.vocab ?? []).map((v) => ({
              kind: 'vocab' as const,
              front: v.w,
              ...(v.r ? { reading: v.r } : {}),
              back: v.en,
            })),
            ...(current.grammar ?? []).map((g) => ({
              kind: 'grammar' as const,
              front: g.p,
              back: g.en,
            })),
          ]);
          setPassedLines((prev) => new Set(prev).add(current.id));
          setTimeout(() => setIndex((i) => Math.min(lines.length - 1, i + 1)), 800);
        }
      },
      onError: () => setListening(false),
    });
    setListening(ok);
    return () => {
      listener.stop();
      listenerRef.current = null;
    };
  }, [line?.id, done]); // eslint-disable-line react-hooks/exhaustive-deps

  const copyLink = () => {
    navigator.clipboard
      .writeText(`${location.origin}/#/p/${slug}`)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      })
      .catch(() => undefined);
  };

  const markPassed = () => {
    if (!line) return;
    setPassedLines((prev) => new Set(prev).add(line.id));
    setIndex((i) => Math.min(lines.length - 1, i + 1));
  };

  return (
    <div className="solo">
      <NightSky className="landing-sky" />
      <div className="solo-card">
        <header className="solo-header">
          <a className="chip" href="#/">
            ← Serifu
          </a>
          <h1 className="solo-title">
            {/* Strip the series prefix so a 390px viewport shows the part
                that identifies THIS scene (audit-01 finding 9). */}
            {script.title.replace('葬送のフリーレン — ', '').replace('葬送のフリーレン ', '')}
          </h1>
          <button className="chip" onClick={copyLink}>
            {copied ? '✓ copied' : 'share ⧉'}
          </button>
        </header>

        <div className="solo-progress muted">
          {Math.min(index + 1, lines.length)} / {lines.length} lines · {passedLines.size} passed
          {attempts > 0 ? ` · ${attempts} attempts` : ''}
        </div>
        <div className="solo-bar">
          <i style={{ width: `${(passedLines.size / lines.length) * 100}%` }} />
        </div>

        {done ? (
          <div className="solo-done">
            <p className="solo-celebrate">🎉 シーン制覇！ You spoke every line.</p>
            <p className="muted">
              {passedLines.size} lines in {attempts} attempts. The words and grammar you passed are
              now in your 習得 mastery tracker.
            </p>
            <div className="row">
              <button
                className="primary"
                onClick={() => {
                  setPassedLines(new Set());
                  setIndex(0);
                  setAttempts(0);
                }}
              >
                ↺ practice again
              </button>
              <a className="chip" href="#/">
                try it with friends →
              </a>
            </div>
            <p className="solo-grammar-link muted">
              <button className="linklike" onClick={() => setGrammarOpen(true)}>
                文法さくいん <small>grammar index</small>
              </button>
            </p>
          </div>
        ) : line ? (
          <div className="solo-line">
            <div className="solo-who" style={{ color: char?.color }}>
              {char?.name ?? '—'}
            </div>
            <p className="jp">
              <RubyText
                tokens={peek ? line.tokens : maskTokens(line.tokens, hideLevel)}
                furigana={settings.furigana && (peek || hideLevel === 0)}
              />
            </p>
            {line.translation && (
              <p className={hideLevel >= 3 ? 'solo-en prompt' : 'solo-en muted'}>{line.translation}</p>
            )}

            <div className="solo-controls">
              <div className="hide-levels" role="group" aria-label="hide level">
                {HIDE_LEVELS.map((label, lvl) => (
                  <button
                    key={label}
                    className={hideLevel === lvl ? 'chip current' : 'chip'}
                    onClick={() => setHideLevel(lvl)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {hideLevel > 0 && (
                <button
                  className="chip"
                  onPointerDown={() => setPeek(true)}
                  onPointerUp={() => setPeek(false)}
                  onPointerLeave={() => setPeek(false)}
                >
                  👁 チラ見 (hold)
                </button>
              )}
              <label className="toggle">
                判定
                <select value={threshold} onChange={(e) => setThreshold(Number(e.target.value))}>
                  <option value={55}>ゆるめ 55+</option>
                  <option value={70}>ふつう 70+</option>
                  <option value={85}>きびしめ 85+</option>
                </select>
              </label>
            </div>

            <div className="speech-status">
              {listening ? (
                <span className="mic-live">🎤 listening… (判定 {threshold}+)</span>
              ) : (
                <span className="muted">
                  {speechSupported()
                    ? 'mic unavailable — use the buttons below'
                    : 'no speech recognition in this browser — read aloud, then mark it'}
                </span>
              )}
              {interim && <span className="speech-interim">「{interim}」</span>}
              {lastScore !== null &&
                (lastScore >= threshold ? (
                  <span className="score-badge pass">🎉 {lastScore}% — 合格！</span>
                ) : (
                  <span className="score-badge fail">
                    {lastScore}% — もう一回！ <small>「{lastHeard.slice(0, 30)}」</small>
                  </span>
                ))}
            </div>

            <LearnPanel line={line} compact />

            <div className="solo-nav">
              <button disabled={index === 0} onClick={() => setIndex((i) => Math.max(0, i - 1))}>
                ← prev
              </button>
              <button onClick={markPassed}>✓ said it — next</button>
              <button
                disabled={index >= lines.length - 1}
                onClick={() => setIndex((i) => Math.min(lines.length - 1, i + 1))}
              >
                skip →
              </button>
            </div>
          </div>
        ) : null}

        {grammarOpen && <GrammarIndex onClose={() => setGrammarOpen(false)} />}

        <footer className="solo-footer muted">
          友達と一緒に観るなら → <a href="#/">create a room</a>
        </footer>
      </div>
    </div>
  );
}
