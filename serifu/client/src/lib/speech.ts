import type { ScriptLine } from '../../../shared/types';

/** Score at or above which a spoken attempt passes and playback auto-resumes. */
export const PASS_SCORE = 70;

/** Katakana -> hiragana (code points shifted by 0x60 within the kana block). */
export function kataToHira(s: string): string {
  let out = '';
  for (const ch of s) {
    const code = ch.codePointAt(0) ?? 0;
    out += code >= 0x30a1 && code <= 0x30f6 ? String.fromCodePoint(code - 0x60) : ch;
  }
  return out;
}

/**
 * Normalize for comparison: lowercase, katakana->hiragana, and keep only
 * hiragana, kanji, the long-vowel mark, and ASCII alphanumerics — recognition
 * output differs from scripts mostly in punctuation and spacing.
 */
export function normalizeJa(s: string): string {
  let out = '';
  for (const ch of kataToHira(s.toLowerCase())) {
    const code = ch.codePointAt(0) ?? 0;
    const isHira = code >= 0x3041 && code <= 0x3096;
    const isKanji = (code >= 0x4e00 && code <= 0x9fff) || code === 0x3005;
    const isChoon = code === 0x30fc;
    const isAlnum = (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9');
    if (isHira || isKanji || isChoon || isAlnum) out += ch;
  }
  return out;
}

export function levenshtein(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;
  let prev = new Array<number>(n + 1);
  let curr = new Array<number>(n + 1);
  for (let j = 0; j <= n; j++) prev[j] = j;
  for (let i = 1; i <= m; i++) {
    curr[0] = i;
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      curr[j] = Math.min((curr[j - 1] ?? 0) + 1, (prev[j] ?? 0) + 1, (prev[j - 1] ?? 0) + cost);
    }
    [prev, curr] = [curr, prev];
  }
  return prev[n] ?? 0;
}

export function similarity(a: string, b: string): number {
  if (a.length === 0 && b.length === 0) return 1;
  const max = Math.max(a.length, b.length);
  return 1 - levenshtein(a, b) / max;
}

/**
 * Score a recognized transcript against a line, 0-100. Compares against both
 * the surface text (kanji) and the reading (furigana substituted in), since
 * recognizers may output either form.
 */
export function scoreAttempt(transcript: string, line: ScriptLine): number {
  const surface = line.tokens.map((t) => t.t).join('');
  const reading = line.tokens.map((t) => t.r ?? t.t).join('');
  const heard = normalizeJa(transcript);
  if (!heard) return 0;
  const best = Math.max(
    similarity(heard, normalizeJa(surface)),
    similarity(heard, normalizeJa(reading))
  );
  return Math.max(0, Math.min(100, Math.round(best * 100)));
}

interface RecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((e: SpeechResultEventLike) => void) | null;
  onerror: ((e: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

interface SpeechResultEventLike {
  resultIndex: number;
  results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }>;
}

export function speechSupported(): boolean {
  const w = window as unknown as Record<string, unknown>;
  return Boolean(w.SpeechRecognition ?? w.webkitSpeechRecognition);
}

export interface ListenHandlers {
  onInterim(text: string): void;
  onFinal(text: string): void;
  onError(message: string): void;
}

/**
 * Thin wrapper over the Web Speech API (Chrome/Edge) that keeps listening
 * until stopped — the engine ends sessions on silence, so we restart it.
 */
export class SpeechListener {
  private rec: RecognitionLike | null = null;
  private active = false;

  start(handlers: ListenHandlers): boolean {
    const w = window as unknown as Record<string, unknown>;
    const Ctor = (w.SpeechRecognition ?? w.webkitSpeechRecognition) as
      | (new () => RecognitionLike)
      | undefined;
    if (!Ctor) return false;
    this.stop();
    const rec = new Ctor();
    this.rec = rec;
    this.active = true;
    rec.lang = 'ja-JP';
    rec.continuous = true;
    rec.interimResults = true;
    rec.onresult = (e) => {
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const result = e.results[i];
        if (!result) continue;
        const text = result[0]?.transcript ?? '';
        if (result.isFinal) handlers.onFinal(text);
        else interim += text;
      }
      if (interim) handlers.onInterim(interim);
    };
    rec.onerror = (e) => {
      // Silence and manual aborts are routine, not errors worth surfacing.
      if (e.error === 'no-speech' || e.error === 'aborted') return;
      handlers.onError(String(e.error ?? 'speech recognition error'));
    };
    rec.onend = () => {
      if (this.active) {
        try {
          rec.start();
        } catch {
          // Already restarted elsewhere; ignore.
        }
      }
    };
    try {
      rec.start();
    } catch {
      this.rec = null;
      this.active = false;
      return false;
    }
    return true;
  }

  stop(): void {
    this.active = false;
    const rec = this.rec;
    this.rec = null;
    if (rec) {
      rec.onend = null;
      rec.onresult = null;
      rec.onerror = null;
      try {
        rec.stop();
      } catch {
        // Stopping an already-stopped recognizer throws in some browsers.
      }
    }
  }
}
