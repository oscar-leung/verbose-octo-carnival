import type { Character, RubyToken, ScriptLine, SkitScript } from '../../../shared/types';

export interface Cue {
  start: number;
  end: number;
  text: string;
  /** Speaker name, when the subtitle format carries one (ASS "Name" field). */
  name?: string;
}

// CJK Unified Ideographs plus the iteration/repetition marks that commonly
// take part in a furigana base. Built with fromCharCode to keep this file
// free of numeric unicode escapes.
const HAN_RANGE = `${String.fromCharCode(0x4e00)}-${String.fromCharCode(0x9fff)}`;
const EXTRA_BASE = '々〆ヵヶ';
const RUBY_PATTERN = new RegExp(
  `(?:[｜|]([^《》｜|]+)|([${HAN_RANGE}${EXTRA_BASE}]+))《([^《》]+)》`,
  'g'
);

/**
 * Parse Aozora-style ruby notation into tokens:
 *   "漢字《かんじ》"      -> reading attaches to the trailing kanji run
 *   "｜お土産《みやげ》"  -> explicit base marked with ｜ (or |)
 * Text without ruby becomes a single plain token.
 */
export function parseRubyText(text: string): RubyToken[] {
  const tokens: RubyToken[] = [];
  let lastIndex = 0;
  RUBY_PATTERN.lastIndex = 0;
  for (let m = RUBY_PATTERN.exec(text); m !== null; m = RUBY_PATTERN.exec(text)) {
    const before = text.slice(lastIndex, m.index);
    if (before) tokens.push({ t: before });
    const base = m[1] ?? m[2] ?? '';
    const reading = m[3] ?? '';
    if (base) tokens.push({ t: base, r: reading });
    lastIndex = m.index + m[0].length;
  }
  const rest = text.slice(lastIndex);
  if (rest) tokens.push({ t: rest });
  if (tokens.length === 0) tokens.push({ t: text });
  return tokens;
}

/** Inverse of parseRubyText, for round-tripping through the editor. */
export function rubyTokensToText(tokens: RubyToken[]): string {
  return tokens
    .map((tok) => (tok.r ? `｜${tok.t}《${tok.r}》` : tok.t))
    .join('');
}

const TIME_PATTERN = new RegExp(
  '(?:([0-9]{1,2}):)?([0-9]{1,2}):([0-9]{2})[,.]([0-9]{1,3})'
);

export function parseTimestamp(raw: string): number | null {
  const m = TIME_PATTERN.exec(raw.trim());
  if (!m) return null;
  const h = m[1] !== undefined ? Number(m[1]) : 0;
  const min = Number(m[2]);
  const s = Number(m[3]);
  const frac = Number((m[4] ?? '0').padEnd(3, '0'));
  return h * 3600 + min * 60 + s + frac / 1000;
}

const NL = String.fromCharCode(10);
const TAG_PATTERN = new RegExp('<[^<>]*>', 'g');

function endsWithAsciiWord(line: string): boolean {
  return /[A-Za-z0-9,.!?'")]$/.test(line);
}

/** Join a cue's text lines: space between Latin lines, nothing between CJK. */
export function joinCueLines(lines: string[]): string {
  let result = '';
  for (const line of lines) {
    if (result && endsWithAsciiWord(result)) result += ' ';
    result += line;
  }
  return result;
}

/**
 * Parse Advanced SubStation Alpha (.ass/.ssa) events into cues. This is the
 * dominant format on Japanese subtitle archives like jimaku.cc. Field order
 * comes from the [Events] Format line; override tags like {\pos(...)} are
 * stripped, and the Name field (when the subber filled it in) is kept as a
 * speaker hint so the editor can pre-assign characters.
 */
export function parseAss(input: string): Cue[] {
  const lines = input
    .replace(new RegExp(String.fromCharCode(0xfeff), 'g'), '')
    .split(new RegExp(String.fromCharCode(13) + '?' + NL));
  // Default V4+ field order, replaced if a Format: line is present.
  let fields = ['Layer', 'Start', 'End', 'Style', 'Name', 'MarginL', 'MarginR', 'MarginV', 'Effect', 'Text'];
  const cues: Cue[] = [];
  const OVERRIDE_TAGS = new RegExp('[{][^{}]*[}]', 'g');
  for (const raw of lines) {
    const line = raw.trim();
    if (/^Format:/i.test(line)) {
      fields = line.slice(line.indexOf(':') + 1).split(',').map((f) => f.trim());
      continue;
    }
    if (!/^Dialogue:/i.test(line)) continue;
    const payload = line.slice(line.indexOf(':') + 1).trimStart();
    const parts = payload.split(',');
    if (parts.length < fields.length) continue;
    const textIndex = fields.indexOf('Text');
    const get = (name: string): string => {
      const i = fields.indexOf(name);
      return i >= 0 ? (parts[i] ?? '').trim() : '';
    };
    // Text is the last field and may itself contain commas.
    const text = (textIndex >= 0 ? parts.slice(textIndex).join(',') : '')
      .replace(OVERRIDE_TAGS, '')
      .split(/\\[Nn]/)
      .map((s) => s.replace(/\\h/g, ' ').trim())
      .filter((s) => s.length > 0)
      .reduce((acc, s) => (acc && endsWithAsciiWord(acc) ? `${acc} ${s}` : acc + s), '');
    if (!text) continue;
    const start = parseTimestamp(get('Start'));
    const end = parseTimestamp(get('End'));
    if (start === null || end === null) continue;
    const name = get('Name');
    cues.push({
      start,
      end: Math.max(start, end),
      text,
      ...(name && name !== '0' ? { name } : {}),
    });
  }
  cues.sort((a, b) => a.start - b.start);
  return cues;
}

/** True when content looks like an ASS/SSA file rather than SRT/VTT. */
export function looksLikeAss(input: string): boolean {
  return /^\s*\[Script Info\]/im.test(input) || /^Dialogue:/m.test(input);
}

/**
 * Parse SRT or WebVTT content into cues. Tolerates missing index lines,
 * VTT headers/NOTE/STYLE blocks, and cue settings after the timestamps.
 * ASS/SSA input is detected and routed to parseAss.
 */
export function parseCues(input: string): Cue[] {
  if (looksLikeAss(input)) return parseAss(input);
  const normalized = input
    .replace(new RegExp(String.fromCharCode(0xfeff), 'g'), '')
    .replace(new RegExp(String.fromCharCode(13) + '?' + NL, 'g'), NL)
    .replace(new RegExp(String.fromCharCode(13), 'g'), NL);
  const blocks = normalized.split(new RegExp(NL + '{2,}'));
  const cues: Cue[] = [];
  for (const block of blocks) {
    const lines = block.split(NL).map((l) => l.trim()).filter((l) => l.length > 0);
    if (lines.length === 0) continue;
    const first = lines[0] ?? '';
    if (first.startsWith('WEBVTT') || first.startsWith('NOTE') || first.startsWith('STYLE')) {
      continue;
    }
    const timeLineIndex = lines.findIndex((l) => l.includes('-->'));
    if (timeLineIndex === -1) continue;
    const timeLine = lines[timeLineIndex] ?? '';
    const [startRaw, endRaw] = timeLine.split('-->');
    const start = parseTimestamp(startRaw ?? '');
    const end = parseTimestamp(endRaw ?? '');
    if (start === null || end === null) continue;
    const textLines = lines
      .slice(timeLineIndex + 1)
      .map((l) => l.replace(TAG_PATTERN, '').trim())
      .filter((l) => l.length > 0);
    if (textLines.length === 0) continue;
    cues.push({ start, end: Math.max(start, end), text: joinCueLines(textLines) });
  }
  cues.sort((a, b) => a.start - b.start);
  return cues;
}

/** Wrap parsed cues into a speakerless script the editor can then tag. */
export function cuesToScript(cues: Cue[], title: string, characters: Character[] = []): SkitScript {
  const lines: ScriptLine[] = cues.map((cue, i) => ({
    id: `l${i + 1}`,
    character: null,
    start: cue.start,
    end: cue.end,
    tokens: parseRubyText(cue.text),
  }));
  return { title, characters, lines };
}
