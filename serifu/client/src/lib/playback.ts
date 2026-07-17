import type { PlaybackState, ScriptLine } from '../../../shared/types';

/** Extrapolated room-video position for a playback state at `serverNowMs`. */
export function expectedPosition(playback: PlaybackState, serverNowMs: number): number {
  if (!playback.isPlaying) return playback.position;
  return playback.position + (serverNowMs - playback.updatedAt) / 1000;
}

/**
 * The line whose window contains `position`. When several overlap, the one
 * that started last wins. Lines are assumed sorted by start time.
 */
export function findActiveLineId(lines: ScriptLine[], position: number): string | null {
  let active: string | null = null;
  for (const line of lines) {
    if (line.start > position + 0.2) break;
    if (position >= line.start - 0.2 && position <= line.end + 0.3) active = line.id;
  }
  return active;
}

/** Seconds -> "m:ss" or "h:mm:ss". */
export function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const total = Math.floor(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const ss = String(s).padStart(2, '0');
  return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${ss}` : `${m}:${ss}`;
}

/**
 * Parse a user-typed time: plain seconds ("83.5"), "m:ss", "h:mm:ss",
 * with "," or "." decimals. Returns null when unparseable.
 */
export function parseTimeInput(raw: string): number | null {
  const text = raw.trim().replace(',', '.');
  if (!text) return null;
  const parts = text.split(':');
  if (parts.length > 3) return null;
  let seconds = 0;
  for (const part of parts) {
    if (!/^[0-9]+(?:[.][0-9]+)?$/.test(part)) return null;
    seconds = seconds * 60 + Number(part);
  }
  return Number.isFinite(seconds) ? seconds : null;
}
