import type { SkitScript } from '../../../shared/types';
import { loadLibrary } from './scriptLibrary';

/**
 * Season/episode tracker: a slot for every episode of the series you're
 * working through. The app ships NO episode transcripts — each slot is
 * filled by importing that episode's subtitles yourself (see README on
 * jimaku.cc), which keeps the app legally clean to distribute.
 */

export interface SeasonDef {
  n: number;
  label: string;
  defaultCount: number;
  airing?: boolean;
}

export const SEASONS: SeasonDef[] = [
  { n: 1, label: 'Season 1 (2023–24)', defaultCount: 28 },
  { n: 2, label: 'Season 2 (2026, airing)', defaultCount: 12, airing: true },
];

export interface EpisodeMeta {
  /** User-editable episode title (auto-suggested from imports). */
  title: string;
  /** Library entry title this episode's prepared script is saved under. */
  scriptTitle?: string;
  practiced?: boolean;
}

export type EpisodeMap = Record<string, EpisodeMeta>;

const KEY = 'serifu:episodes';
const COUNT_KEY = 'serifu:episodeCounts';

export const episodeKey = (season: number, episode: number): string => `s${season}e${episode}`;

export function loadEpisodes(): EpisodeMap {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : {};
    return typeof parsed === 'object' && parsed !== null ? (parsed as EpisodeMap) : {};
  } catch {
    return {};
  }
}

export function saveEpisode(key: string, meta: EpisodeMeta): EpisodeMap {
  const all = loadEpisodes();
  all[key] = meta;
  try {
    localStorage.setItem(KEY, JSON.stringify(all));
  } catch {
    // storage unavailable — session-only
  }
  return all;
}

/** Per-season episode counts, extendable as new episodes air. */
export function loadCounts(): Record<number, number> {
  try {
    const raw = localStorage.getItem(COUNT_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : {};
    const counts: Record<number, number> = {};
    for (const s of SEASONS) {
      const v = (parsed as Record<string, unknown>)[String(s.n)];
      counts[s.n] = typeof v === 'number' && v >= s.defaultCount ? v : s.defaultCount;
    }
    return counts;
  } catch {
    return Object.fromEntries(SEASONS.map((s) => [s.n, s.defaultCount]));
  }
}

export function saveCount(season: number, count: number): void {
  const counts = loadCounts();
  counts[season] = count;
  try {
    localStorage.setItem(COUNT_KEY, JSON.stringify(counts));
  } catch {
    // ignore
  }
}

/** The library script linked to an episode, if it exists. */
export function scriptForEpisode(meta: EpisodeMeta | undefined): SkitScript | null {
  if (!meta?.scriptTitle) return null;
  return loadLibrary().find((e) => e.title === meta.scriptTitle)?.script ?? null;
}
