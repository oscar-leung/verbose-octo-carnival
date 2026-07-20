import type { VocabItem } from '../../../shared/types';

/**
 * Personal word list, saved per browser. Words are added from a line's
 * vocab panel while practicing and exported as CSV for Anki or a spreadsheet.
 */

export interface WordEntry extends VocabItem {
  addedAt: number;
}

const KEY = 'serifu:wordbook';
const MAX_WORDS = 2000;

export function loadWordbook(): WordEntry[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (e): e is WordEntry =>
        typeof e === 'object' &&
        e !== null &&
        typeof (e as WordEntry).w === 'string' &&
        typeof (e as WordEntry).en === 'string'
    );
  } catch {
    return [];
  }
}

function persist(entries: WordEntry[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(entries.slice(0, MAX_WORDS)));
  } catch {
    // Storage full or blocked — the in-memory session still works.
  }
}

export function hasWord(w: string): boolean {
  return loadWordbook().some((e) => e.w === w);
}

export function addWord(item: VocabItem): void {
  const entries = loadWordbook().filter((e) => e.w !== item.w);
  entries.unshift({ ...item, addedAt: Date.now() });
  persist(entries);
}

export function removeWord(w: string): void {
  persist(loadWordbook().filter((e) => e.w !== w));
}

export function clearWordbook(): void {
  persist([]);
}

/** CSV with a header row: word, reading, meaning. Anki maps these to fields. */
export function wordbookToCsv(entries: WordEntry[]): string {
  const esc = (s: string) => `"${s.replace(/"/g, '""')}"`;
  const NL = String.fromCharCode(10);
  const rows = entries.map((e) => [esc(e.w), esc(e.r ?? ''), esc(e.en)].join(','));
  return ['word,reading,meaning', ...rows].join(NL) + NL;
}
