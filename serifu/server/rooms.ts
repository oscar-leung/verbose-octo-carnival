import type {
  PlaybackState,
  RoomState,
  RoomUser,
  SkitScript,
} from '../shared/types';
import { MAX_USERS_PER_ROOM } from '../shared/types';

const USER_COLORS = [
  '#7ecbff',
  '#ffb86c',
  '#a6e3a1',
  '#f38ba8',
  '#cba6f7',
  '#f9e2af',
  '#94e2d5',
  '#eba0ac',
  '#b4befe',
  '#fab387',
  '#89dceb',
  '#f5c2e7',
];

/** How long after a rehearsal resume the same line cannot re-trigger a pause. */
const REHEARSAL_COOLDOWN_MS = 8_000;

export interface Room {
  id: string;
  users: Map<string, RoomUser>;
  /** characterId -> userId */
  claims: Map<string, string>;
  rehearsalEnabled: boolean;
  playback: PlaybackState;
  script: SkitScript | null;
  scriptVersion: number;
  /** lineId -> ms timestamp of its last rehearsal resume. */
  rehearsalCooldowns: Map<string, number>;
  emptySince: number | null;
}

function sanitizeName(raw: string): string {
  const cleaned = raw.replace(/[\u0000-\u001f\u007f]/g, '').trim();
  return (cleaned || 'ゲスト').slice(0, 24);
}

function clampPosition(position: number): number {
  if (!Number.isFinite(position)) return 0;
  // 10 hours is beyond any episode; guards absurd client input.
  return Math.min(Math.max(position, 0), 36_000);
}

export function validateScript(script: unknown): string | null {
  if (typeof script !== 'object' || script === null) return 'script must be an object';
  const s = script as Record<string, unknown>;
  if (typeof s.title !== 'string' || s.title.length > 200) {
    return 'title must be a string of at most 200 characters';
  }
  if (!Array.isArray(s.characters) || s.characters.length > 50) {
    return 'characters must be an array of at most 50 entries';
  }
  const charIds = new Set<string>();
  for (const c of s.characters) {
    if (typeof c !== 'object' || c === null) return 'character entries must be objects';
    const ch = c as Record<string, unknown>;
    if (typeof ch.id !== 'string' || !ch.id || ch.id.length > 64) {
      return 'character ids must be non-empty strings';
    }
    if (typeof ch.name !== 'string' || !ch.name || ch.name.length > 64) {
      return 'character names must be non-empty strings';
    }
    if (typeof ch.color !== 'string' || ch.color.length > 32) {
      return 'character colors must be strings';
    }
    if (charIds.has(ch.id)) return `duplicate character id: ${ch.id}`;
    charIds.add(ch.id);
  }
  if (!Array.isArray(s.lines) || s.lines.length > 5000) {
    return 'lines must be an array of at most 5000 entries';
  }
  const lineIds = new Set<string>();
  for (const l of s.lines) {
    if (typeof l !== 'object' || l === null) return 'line entries must be objects';
    const line = l as Record<string, unknown>;
    if (typeof line.id !== 'string' || !line.id || line.id.length > 64) {
      return 'line ids must be non-empty strings';
    }
    if (lineIds.has(line.id)) return `duplicate line id: ${line.id}`;
    lineIds.add(line.id);
    if (line.character !== null && typeof line.character !== 'string') {
      return 'line.character must be a string or null';
    }
    if (
      typeof line.start !== 'number' ||
      typeof line.end !== 'number' ||
      !Number.isFinite(line.start) ||
      !Number.isFinite(line.end) ||
      line.start < 0 ||
      line.end < line.start
    ) {
      return 'line start/end must be finite numbers with 0 <= start <= end';
    }
    if (!Array.isArray(line.tokens) || line.tokens.length > 200) {
      return 'line tokens must be an array of at most 200 entries';
    }
    for (const t of line.tokens) {
      if (typeof t !== 'object' || t === null) return 'tokens must be objects';
      const tok = t as Record<string, unknown>;
      if (typeof tok.t !== 'string' || tok.t.length > 500) {
        return 'token text must be a string of at most 500 characters';
      }
      if (tok.r !== undefined && (typeof tok.r !== 'string' || tok.r.length > 200)) {
        return 'token readings must be strings of at most 200 characters';
      }
    }
    if (
      line.translation !== undefined &&
      (typeof line.translation !== 'string' || line.translation.length > 1000)
    ) {
      return 'line translations must be strings of at most 1000 characters';
    }
  }
  return null;
}

export class RoomStore {
  private rooms = new Map<string, Room>();

  constructor(private now: () => number = Date.now) {}

  get(roomId: string): Room | undefined {
    return this.rooms.get(roomId);
  }

  private getOrCreate(roomId: string): Room {
    let room = this.rooms.get(roomId);
    if (!room) {
      room = {
        id: roomId,
        users: new Map(),
        claims: new Map(),
        rehearsalEnabled: true,
        playback: {
          isPlaying: false,
          position: 0,
          updatedAt: this.now(),
          pausedForLineId: null,
        },
        script: null,
        scriptVersion: 0,
        rehearsalCooldowns: new Map(),
        emptySince: null,
      };
      this.rooms.set(roomId, room);
    }
    return room;
  }

  /** Current room-video position, extrapolated while playing. */
  currentPosition(room: Room): number {
    const { isPlaying, position, updatedAt } = room.playback;
    if (!isPlaying) return position;
    return position + (this.now() - updatedAt) / 1000;
  }

  join(roomId: string, userId: string, rawName: string): RoomUser | { error: string } {
    const room = this.getOrCreate(roomId);
    if (room.users.size >= MAX_USERS_PER_ROOM && !room.users.has(userId)) {
      return { error: `Room is full (max ${MAX_USERS_PER_ROOM} people).` };
    }
    const user: RoomUser = {
      id: userId,
      name: sanitizeName(rawName),
      color: USER_COLORS[room.users.size % USER_COLORS.length] ?? '#8899aa',
      inVoice: false,
      muted: false,
    };
    room.users.set(userId, user);
    room.emptySince = null;
    return user;
  }

  leave(roomId: string, userId: string): boolean {
    const room = this.rooms.get(roomId);
    if (!room || !room.users.delete(userId)) return false;
    for (const [charId, ownerId] of room.claims) {
      if (ownerId === userId) room.claims.delete(charId);
    }
    if (room.users.size === 0) {
      room.emptySince = this.now();
      // Nobody left to hold a paused state; leave playback as-is otherwise.
      room.playback.pausedForLineId = null;
    }
    return true;
  }

  play(roomId: string, position: number): boolean {
    const room = this.rooms.get(roomId);
    if (!room) return false;
    room.playback = {
      isPlaying: true,
      position: clampPosition(position),
      updatedAt: this.now(),
      pausedForLineId: null,
    };
    return true;
  }

  pause(roomId: string, position: number): boolean {
    const room = this.rooms.get(roomId);
    if (!room) return false;
    room.playback = {
      isPlaying: false,
      position: clampPosition(position),
      updatedAt: this.now(),
      pausedForLineId: null,
    };
    return true;
  }

  seek(roomId: string, position: number): boolean {
    const room = this.rooms.get(roomId);
    if (!room) return false;
    const target = clampPosition(position);
    // Seeking backwards means "replay this part" — allow rehearsal pauses again.
    if (target < this.currentPosition(room)) {
      room.rehearsalCooldowns.clear();
    }
    room.playback = {
      isPlaying: room.playback.isPlaying,
      position: target,
      updatedAt: this.now(),
      pausedForLineId: null,
    };
    return true;
  }

  setRehearsal(roomId: string, enabled: boolean): boolean {
    const room = this.rooms.get(roomId);
    if (!room) return false;
    room.rehearsalEnabled = enabled;
    if (!enabled) room.playback.pausedForLineId = null;
    return true;
  }

  /**
   * Auto-pause playback at the start of a claimed line. Any client may report
   * the line crossing; the server dedupes and validates.
   */
  rehearsalPause(roomId: string, lineId: string): boolean {
    const room = this.rooms.get(roomId);
    if (!room || !room.rehearsalEnabled || !room.script) return false;
    if (!room.playback.isPlaying) return false;
    const line = room.script.lines.find((l) => l.id === lineId);
    if (!line || line.character === null) return false;
    if (!room.claims.has(line.character)) return false;
    const cooldownAt = room.rehearsalCooldowns.get(lineId);
    if (cooldownAt !== undefined && this.now() - cooldownAt < REHEARSAL_COOLDOWN_MS) {
      return false;
    }
    // Only pause if playback is actually near this line — a stale report from a
    // badly-drifted client should not yank the room around.
    const pos = this.currentPosition(room);
    if (Math.abs(pos - line.start) > 5) return false;
    room.playback = {
      isPlaying: false,
      position: line.start,
      updatedAt: this.now(),
      pausedForLineId: lineId,
    };
    return true;
  }

  rehearsalResume(roomId: string): boolean {
    const room = this.rooms.get(roomId);
    if (!room || room.playback.pausedForLineId === null) return false;
    room.rehearsalCooldowns.set(room.playback.pausedForLineId, this.now());
    room.playback = {
      isPlaying: true,
      position: room.playback.position,
      updatedAt: this.now(),
      pausedForLineId: null,
    };
    return true;
  }

  claim(roomId: string, characterId: string, userId: string): boolean {
    const room = this.rooms.get(roomId);
    if (!room || !room.users.has(userId) || !room.script) return false;
    if (!room.script.characters.some((c) => c.id === characterId)) return false;
    const owner = room.claims.get(characterId);
    if (owner !== undefined && owner !== userId) return false;
    room.claims.set(characterId, userId);
    return true;
  }

  release(roomId: string, characterId: string, userId: string): boolean {
    const room = this.rooms.get(roomId);
    if (!room || room.claims.get(characterId) !== userId) return false;
    room.claims.delete(characterId);
    return true;
  }

  setVoice(roomId: string, userId: string, inVoice: boolean, muted: boolean): boolean {
    const room = this.rooms.get(roomId);
    const user = room?.users.get(userId);
    if (!room || !user) return false;
    user.inVoice = inVoice;
    user.muted = muted;
    return true;
  }

  loadScript(roomId: string, script: SkitScript): string | null {
    const room = this.rooms.get(roomId);
    if (!room) return 'room not found';
    const error = validateScript(script);
    if (error) return error;
    const sorted: SkitScript = {
      ...script,
      lines: [...script.lines].sort((a, b) => a.start - b.start),
    };
    room.script = sorted;
    room.scriptVersion += 1;
    room.rehearsalCooldowns.clear();
    room.playback.pausedForLineId = null;
    const validChars = new Set(sorted.characters.map((c) => c.id));
    for (const charId of [...room.claims.keys()]) {
      if (!validChars.has(charId)) room.claims.delete(charId);
    }
    return null;
  }

  toState(roomId: string): RoomState | null {
    const room = this.rooms.get(roomId);
    if (!room) return null;
    return {
      roomId: room.id,
      users: [...room.users.values()],
      claims: Object.fromEntries(room.claims),
      rehearsalEnabled: room.rehearsalEnabled,
      playback: { ...room.playback },
      scriptTitle: room.script?.title ?? null,
      scriptVersion: room.scriptVersion,
      serverNow: this.now(),
    };
  }

  /** Remove rooms that have been empty for longer than `maxEmptyMs`. */
  gc(maxEmptyMs: number): number {
    let removed = 0;
    for (const [id, room] of this.rooms) {
      if (
        room.users.size === 0 &&
        room.emptySince !== null &&
        this.now() - room.emptySince > maxEmptyMs
      ) {
        this.rooms.delete(id);
        removed += 1;
      }
    }
    return removed;
  }
}
