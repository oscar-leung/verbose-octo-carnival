import type { SkitScript } from '../../../shared/types';

/**
 * A tiny per-browser library of prepared episode scripts, so each episode of
 * a season only has to be imported/tagged once and can be reloaded into any
 * room in one click. Stored in localStorage; export JSON to share with friends.
 */

export interface LibraryEntry {
  title: string;
  savedAt: number;
  script: SkitScript;
}

const LIBRARY_KEY = 'serifu:library';
const MAX_ENTRIES = 60;

export function loadLibrary(): LibraryEntry[] {
  try {
    const raw = localStorage.getItem(LIBRARY_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (e): e is LibraryEntry =>
        typeof e === 'object' &&
        e !== null &&
        typeof (e as LibraryEntry).title === 'string' &&
        typeof (e as LibraryEntry).savedAt === 'number' &&
        typeof (e as LibraryEntry).script === 'object'
    );
  } catch {
    return [];
  }
}

function persist(entries: LibraryEntry[]): boolean {
  try {
    localStorage.setItem(LIBRARY_KEY, JSON.stringify(entries));
    return true;
  } catch {
    return false; // quota exceeded or private mode
  }
}

/** Saves (or replaces, by title) a script. Returns false if storage failed. */
export function saveToLibrary(script: SkitScript): boolean {
  const entries = loadLibrary().filter((e) => e.title !== script.title);
  entries.unshift({ title: script.title, savedAt: Date.now(), script });
  return persist(entries.slice(0, MAX_ENTRIES));
}

export function removeFromLibrary(title: string): void {
  persist(loadLibrary().filter((e) => e.title !== title));
}
