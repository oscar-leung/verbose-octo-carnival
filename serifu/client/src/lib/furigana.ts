import type { RubyToken } from '../../../shared/types';

// Auto-furigana: turn plain Japanese text into RubyToken[] using kuromoji's
// morphological analysis. The analyzer + its ~17MB dictionary are loaded
// lazily (dynamic import + CDN fetch) only when the feature is first used,
// so the main bundle stays free of kuromoji. The conversion helpers below
// are pure and unit-tested without the dictionary.
//
// Note: package.json aliases "path" -> path-browserify because kuromoji's
// dictionary loader calls path.join in the browser; Node still resolves
// the builtin for server code, so only the Vite bundle sees the alias.

/** CDN home of the IPADIC dictionary files — never committed to the repo. */
export const KUROMOJI_DIC_URL = 'https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/dict/';

// Character ranges built with fromCharCode to keep this file free of
// numeric unicode escapes (same convention as srt.ts).
const HIRA_START = 0x3041;
const HIRA_END = 0x3096;
const KATA_START = 0x30a1;
const KATA_END = 0x30f6;
const HAN_RANGE = `${String.fromCharCode(0x4e00)}-${String.fromCharCode(0x9fff)}`;
// Iteration marks and small counters that behave like kanji in a ruby base.
const KANJI_PATTERN = new RegExp(`[${HAN_RANGE}々〆ヵヶ]`);

/** True when the string contains at least one kanji (or 々/〆-style mark). */
export function hasKanji(text: string): boolean {
  return KANJI_PATTERN.test(text);
}

/** Convert katakana to hiragana (kuromoji readings are katakana). */
export function kataToHira(text: string): string {
  let out = '';
  for (const ch of text) {
    const code = ch.charCodeAt(0);
    out += code >= KATA_START && code <= KATA_END ? String.fromCharCode(code - 0x60) : ch;
  }
  return out;
}

function isKanaChar(ch: string): boolean {
  const code = ch.charCodeAt(0);
  return (
    (code >= HIRA_START && code <= HIRA_END) ||
    (code >= KATA_START && code <= KATA_END) ||
    ch === 'ー'
  );
}

/**
 * Split one morpheme into ruby tokens, keeping the reading only over the
 * kanji portion when the surface mixes okurigana. Handles the common cases
 * by stripping matching leading/trailing kana from surface and reading:
 *   食べる/たべる  -> [食(た), べる]
 *   お茶/おちゃ    -> [お, 茶(ちゃ)]
 *   見送った/みおくった -> [見送(みおく), った]
 * Interior kana (言い訳) keeps the whole-surface reading.
 */
export function splitOkurigana(surface: string, readingHira: string): RubyToken[] {
  let lead = 0;
  while (
    lead < surface.length &&
    lead < readingHira.length &&
    isKanaChar(surface[lead] ?? '') &&
    kataToHira(surface[lead] ?? '') === readingHira[lead]
  ) {
    lead++;
  }
  let trail = 0;
  while (
    trail < surface.length - lead &&
    trail < readingHira.length - lead &&
    isKanaChar(surface[surface.length - 1 - trail] ?? '') &&
    kataToHira(surface[surface.length - 1 - trail] ?? '') ===
      readingHira[readingHira.length - 1 - trail]
  ) {
    trail++;
  }
  const core = surface.slice(lead, surface.length - trail);
  const coreReading = readingHira.slice(lead, readingHira.length - trail);
  if (!core || !coreReading || kataToHira(core) === coreReading) {
    // Nothing left to annotate (all-kana token, or a degenerate split).
    return kataToHira(surface) === readingHira || !readingHira
      ? [{ t: surface }]
      : [{ t: surface, r: readingHira }];
  }
  const tokens: RubyToken[] = [];
  if (lead > 0) tokens.push({ t: surface.slice(0, lead) });
  tokens.push({ t: core, r: coreReading });
  if (trail > 0) tokens.push({ t: surface.slice(surface.length - trail) });
  return tokens;
}

/** Merge adjacent tokens that carry no reading into one plain token. */
export function mergePlainTokens(tokens: RubyToken[]): RubyToken[] {
  const merged: RubyToken[] = [];
  for (const tok of tokens) {
    const last = merged[merged.length - 1];
    if (!tok.r && last && !last.r) last.t += tok.t;
    else merged.push(tok.r ? { t: tok.t, r: tok.r } : { t: tok.t });
  }
  return merged;
}

/** The slice of a kuromoji token this module needs (mockable in tests). */
export interface Morpheme {
  surface_form: string;
  /** Katakana reading; missing or '*' for unknown words and symbols. */
  reading?: string;
}

/**
 * Convert analyzed morphemes into RubyToken[]: kanji-bearing surfaces get
 * hiragana readings (okurigana split off), everything else stays plain,
 * and runs of plain tokens are merged.
 */
export function morphemesToRubyTokens(morphemes: Morpheme[]): RubyToken[] {
  const tokens: RubyToken[] = [];
  for (const m of morphemes) {
    const surface = m.surface_form;
    if (!surface) continue;
    const reading = m.reading && m.reading !== '*' ? kataToHira(m.reading) : '';
    if (!reading || !hasKanji(surface)) tokens.push({ t: surface });
    else tokens.push(...splitOkurigana(surface, reading));
  }
  return mergePlainTokens(tokens);
}

interface KuromojiTokenizer {
  tokenize(text: string): Morpheme[];
}

let tokenizerPromise: Promise<KuromojiTokenizer> | null = null;

/**
 * Load kuromoji + its dictionary from the CDN, once. The dynamic import
 * keeps kuromoji out of the main bundle; a failed load (offline) clears
 * the cache so a later attempt can retry.
 */
export function loadTokenizer(): Promise<KuromojiTokenizer> {
  if (!tokenizerPromise) {
    tokenizerPromise = import('kuromoji').then(
      (mod) =>
        new Promise<KuromojiTokenizer>((resolve, reject) => {
          mod.default.builder({ dicPath: KUROMOJI_DIC_URL }).build((err, tokenizer) => {
            if (err) reject(err instanceof Error ? err : new Error(String(err)));
            else resolve(tokenizer);
          });
        })
    );
    tokenizerPromise.catch(() => {
      tokenizerPromise = null;
    });
  }
  return tokenizerPromise;
}

/** Tokenize plain Japanese text into RubyToken[] with auto furigana. */
export async function tokenizeToRuby(text: string): Promise<RubyToken[]> {
  const tokenizer = await loadTokenizer();
  return morphemesToRubyTokens(tokenizer.tokenize(text));
}
