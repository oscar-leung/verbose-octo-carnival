// Shared domain + socket protocol types for Serifu.
// This file must stay free of DOM and Node types — it compiles under both
// the client and server tsconfigs.

/** One inline segment of a line. `r` is the furigana reading shown above `t`. */
export interface RubyToken {
  t: string;
  r?: string;
}

export interface Character {
  id: string;
  name: string;
  color: string;
}

export interface ScriptLine {
  id: string;
  /** Character id, or null for narration / not-yet-assigned lines. */
  character: string | null;
  /** Start/end in seconds of room-video time. */
  start: number;
  end: number;
  tokens: RubyToken[];
  translation?: string;
}

export interface SkitScript {
  title: string;
  characters: Character[];
  lines: ScriptLine[];
}

export interface RoomUser {
  id: string;
  name: string;
  color: string;
  inVoice: boolean;
  muted: boolean;
}

export interface PlaybackState {
  isPlaying: boolean;
  /** Room-video position in seconds at the moment of `updatedAt`. */
  position: number;
  /** Server clock (ms epoch) when `position` was recorded. */
  updatedAt: number;
  /** Set while playback is auto-paused so this line can be acted out. */
  pausedForLineId: string | null;
}

export interface RoomState {
  roomId: string;
  users: RoomUser[];
  /** characterId -> userId */
  claims: Record<string, string>;
  rehearsalEnabled: boolean;
  playback: PlaybackState;
  scriptTitle: string | null;
  scriptVersion: number;
  /** Server clock at broadcast time; lets clients estimate clock offset. */
  serverNow: number;
}

/** One spoken attempt at a line, scored client-side and shared with the room. */
export interface SpeechAttempt {
  lineId: string;
  transcript: string;
  score: number;
  passed: boolean;
}

/** WebRTC signaling payload relayed verbatim between two peers. */
export interface SignalData {
  description?: { type: string; sdp?: string } | null;
  candidate?: Record<string, unknown> | null;
}

export interface JoinAck {
  ok: true;
  selfId: string;
  state: RoomState;
  script: SkitScript | null;
}

export interface JoinError {
  ok: false;
  error: string;
}

export interface ClientToServerEvents {
  'room:join': (
    p: { roomId: string; name: string },
    ack: (r: JoinAck | JoinError) => void
  ) => void;
  'playback:play': (p: { position: number }) => void;
  'playback:pause': (p: { position: number }) => void;
  'playback:seek': (p: { position: number }) => void;
  'rehearsal:set': (p: { enabled: boolean }) => void;
  'rehearsal:pause': (p: { lineId: string }) => void;
  'rehearsal:resume': () => void;
  'character:claim': (p: { characterId: string }) => void;
  'character:release': (p: { characterId: string }) => void;
  'script:load': (
    p: { script: SkitScript },
    ack: (r: { ok: boolean; error?: string }) => void
  ) => void;
  'voice:state': (p: { inVoice: boolean; muted: boolean }) => void;
  'webrtc:signal': (p: { to: string; data: SignalData }) => void;
  'speech:attempt': (p: SpeechAttempt) => void;
}

export interface ServerToClientEvents {
  'room:state': (state: RoomState) => void;
  'script:state': (script: SkitScript | null) => void;
  'webrtc:signal': (p: { from: string; data: SignalData }) => void;
  'speech:attempt': (p: SpeechAttempt & { userId: string; userName: string }) => void;
}

export const ROOM_ID_PATTERN = /^[a-z0-9-]{3,32}$/i;
export const MAX_USERS_PER_ROOM = 12;
export const MAX_SCRIPT_JSON_BYTES = 1_500_000;
