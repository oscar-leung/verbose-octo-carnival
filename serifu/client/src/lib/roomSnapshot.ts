// Per-room localStorage snapshots so a Render free-tier restart (which wipes
// the in-memory rooms) doesn't cost the room its script, claims, or settings.
// Every client keeps its own copy; on rejoining an empty room it offers a
// one-tap restore. Claims are keyed by NAME (character name -> user name)
// because socket ids change across reconnects.
//
// Pure logic only touches plain values; localStorage lives in the thin
// load/save wrappers at the bottom (same pattern as mastery.ts/settings.ts).

import type { RoomState, SkitScript } from '../../../shared/types';
import { MAX_SCRIPT_JSON_BYTES } from '../../../shared/types';

export interface RoomSnapshot {
  /** The full script that was loaded in the room. */
  script: SkitScript;
  /** character NAME -> user NAME (ids change across reconnects). */
  claims: Record<string, string>;
  passScore: number;
  rehearsalEnabled: boolean;
  /** ms epoch when the snapshot was written. */
  savedAt: number;
}

/** Snapshots older than this are not offered for restore. */
export const SNAPSHOT_TTL_MS = 24 * 60 * 60 * 1000;

/** Script cap plus headroom for claims/settings; bigger snapshots are skipped. */
export const MAX_SNAPSHOT_BYTES = MAX_SCRIPT_JSON_BYTES + 100_000;

export function snapshotKey(roomId: string): string {
  return `serifu:roomSnapshot:${roomId}`;
}

/**
 * Build a snapshot from the live room. Claims are translated from
 * characterId -> userId into characterName -> userName; entries whose
 * character or user can't be resolved are dropped.
 */
export function buildRoomSnapshot(
  script: SkitScript,
  state: Pick<RoomState, 'claims' | 'passScore' | 'rehearsalEnabled' | 'users'>,
  savedAt: number
): RoomSnapshot {
  const charNameById = new Map(script.characters.map((c) => [c.id, c.name]));
  const userNameById = new Map(state.users.map((u) => [u.id, u.name]));
  const claims: Record<string, string> = {};
  for (const [charId, userId] of Object.entries(state.claims)) {
    const charName = charNameById.get(charId);
    const userName = userNameById.get(userId);
    if (charName !== undefined && userName !== undefined) claims[charName] = userName;
  }
  return {
    script,
    claims,
    passScore: state.passScore,
    rehearsalEnabled: state.rehearsalEnabled,
    savedAt,
  };
}

/**
 * Parse + shape-check a stored snapshot. Returns null for anything that
 * doesn't look like one (corrupt JSON, missing fields, wrong types). The
 * script itself is only structurally sniffed here — the server re-validates
 * it in full when the restore actually loads it.
 */
export function parseRoomSnapshot(raw: string | null): RoomSnapshot | null {
  if (!raw) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (typeof parsed !== 'object' || parsed === null) return null;
  const s = parsed as Record<string, unknown>;
  if (typeof s.script !== 'object' || s.script === null) return null;
  const script = s.script as Record<string, unknown>;
  if (
    typeof script.title !== 'string' ||
    !Array.isArray(script.characters) ||
    !Array.isArray(script.lines)
  ) {
    return null;
  }
  if (typeof s.claims !== 'object' || s.claims === null || Array.isArray(s.claims)) return null;
  for (const v of Object.values(s.claims)) {
    if (typeof v !== 'string') return null;
  }
  if (typeof s.passScore !== 'number' || !Number.isFinite(s.passScore)) return null;
  if (typeof s.rehearsalEnabled !== 'boolean') return null;
  if (typeof s.savedAt !== 'number' || !Number.isFinite(s.savedAt)) return null;
  return {
    script: s.script as unknown as SkitScript,
    claims: s.claims as Record<string, string>,
    passScore: s.passScore,
    rehearsalEnabled: s.rehearsalEnabled,
    savedAt: s.savedAt,
  };
}

/** Fresh enough to offer a restore? (also rejects clock-skewed future stamps) */
export function isSnapshotFresh(snapshot: RoomSnapshot, now: number): boolean {
  const age = now - snapshot.savedAt;
  return age >= 0 && age < SNAPSHOT_TTL_MS;
}

/**
 * Character ids (in the snapshot's script) that `userName` had claimed.
 * Used so each user re-claims only their OWN roles on restore; friends
 * re-claim theirs when they accept their own prompts.
 */
export function ownClaimedCharacterIds(snapshot: RoomSnapshot, userName: string): string[] {
  const mine = new Set(
    Object.entries(snapshot.claims)
      .filter(([, owner]) => owner === userName)
      .map(([charName]) => charName)
  );
  return snapshot.script.characters.filter((c) => mine.has(c.name)).map((c) => c.id);
}

// ---- localStorage wrappers (no-ops when storage is unavailable) ----

export function saveRoomSnapshot(roomId: string, snapshot: RoomSnapshot): void {
  try {
    const json = JSON.stringify(snapshot);
    if (json.length > MAX_SNAPSHOT_BYTES) return; // too big to be worth caching
    localStorage.setItem(snapshotKey(roomId), json);
  } catch {
    // Private-mode/quota failures are fine to ignore.
  }
}

export function loadRoomSnapshot(roomId: string): RoomSnapshot | null {
  try {
    return parseRoomSnapshot(localStorage.getItem(snapshotKey(roomId)));
  } catch {
    return null;
  }
}
